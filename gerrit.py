#!/usr/bin/python
# coding:utf-8

from __future__ import unicode_literals
from __future__ import print_function
import subprocess
from optparse import OptionParser
import json
import os
import time
import datetime
import tempfile

import sys
if sys.version_info[0] == 2:
    reload(sys)
    sys.setdefaultencoding('utf-8')

# 1. Init version
#    Tony Teng
# 2. Add ChangeID check, get user name from git user.email,
#    Weichuan Yan, 2011-01-06
# 3. Support parameters to set reviewers and review status,
#    Carton He
# 4. Upgrade to Python version, fix the git server change
#    relate issues, Weichuan Yan, 2015-07-16

class ChangeIDError(Exception):
    def __init__(self, msg=''):
        self.msg = msg
    def __str__(self):
        return self.msg

class SignError(Exception):
    def __init__(self, msg=''):
        self.msg = msg
    def __str__(self):
        return self.msg

class GitError(Exception):
    pass

class SSHError(Exception):
    pass

class Gerrit():
    UPDATE_INTERVAL = 7
    def __init__(self, argv):
        self.argv = argv
        self.user = ''
        self.remote = ''
        self.project = ''
        self.commit_ids = []
        self.gerrit_port = '29418'
        self.protocol = ''
        self.server = ''

        self.reviewer = ''
        self.comments = ''
        self.review = False
        self.verify = False
        self.branch = ''
        self.email = 'marvell.com'
        self.update_candidate_branch = False

    def _parse_option(self, argv):
        usage = "\n  %prog [options] branch" 
        parser = OptionParser(usage)
        parser.add_option("-r", "--reviewer", dest = "reviewer",
                type="string", default='', help = "set reviewer list by comma seperator")
        parser.add_option("-c", "--code-review", action="store_true",
                dest = "review", default=False, help = "set gerrit Code-Review +1")
        parser.add_option("-v", "--verify", action="store_true",
                dest = "verify", default=False, help = "set gerrit Verified +1")
        parser.add_option("-m", "--comments", dest = "comments",
                type="string", default='', help = "set comments message")
        parser.add_option("-u", "--user", dest = "user", type="string",
                default='', help = "set gerrit user")
        parser.add_option("-e", "--email", dest = "email", type="string",
                default='', help = "set reviews email suffix, like marvell.com")
        parser.add_option("-f", "--force-update", action="store_true",
                dest = "update", default=False, help = "force update branch candidate list")

        (options, args) = parser.parse_args()
        error_check = [options.reviewer, options.user, options.comments, options.email]
        for opt in error_check:
            if opt.startswith('-'):
                parser.print_help()
                parser.exit()

        if options.reviewer != '':
            self.reviewer = options.reviewer
        self.review = options.review
        self.verify = options.verify
        self.comments = options.comments
        self.update_candidate_branch = options.update
        if options.user != '':
            self.user = options.user
        if options.email != '':
            self.email = options.email
        if (options.update and len(args) > 1) or (not options.update and len(args) != 1):
            parser.print_help()
            parser.exit()
        if len(args) == 1:
            self.branch = args[0]

    def _cmd(self, cmd):
        ret = 1
        msg = []
        out_temp = None
        try:
            if sys.version_info[0] == 3:
                out_temp = tempfile.SpooledTemporaryFile(mode='w+', buffering=2*1024*1024, encoding='utf-8')
            else:
                out_temp = tempfile.SpooledTemporaryFile(bufsize=2*1024*1024)
            out_fd = out_temp.fileno()
            p = subprocess.Popen(cmd, shell=True, stdout=out_fd, stderr=out_fd)
            p.wait()
            out_temp.seek(0)
            msg = out_temp.readlines()
            ret = p.returncode
        except Exception as e:
            print(e)
        finally:
            if out_temp:
                out_temp.close()
        return ret, msg

    def _check_git(self):
        cmd = 'git status'
        ret, lines = self._cmd(cmd)
        if ret != 0:
            raise GitError

    def _update_gerrit_branches(self):
        delta = datetime.timedelta(days=self.UPDATE_INTERVAL + 1)
        gerrit_branch_file = os.path.expanduser('~/.gerrit')
        if os.path.exists(gerrit_branch_file):
            mtime = os.path.getmtime(gerrit_branch_file)
            d1 = datetime.datetime.fromtimestamp(mtime)  
            d2 = datetime.datetime.now()
            delta = d2 - d1
            if delta.days > self.UPDATE_INTERVAL:
                self.update_candidate_branch = True
        else:
            self.update_candidate_branch = True

        if self.update_candidate_branch:
            d = datetime.datetime.now() - datetime.timedelta(days=30)
            query_cmd = 'ssh {}@{} -p {} gerrit query --format=JSON  after:{} status:merged'
            cmd = query_cmd.format(self.user, self.server, self.gerrit_port, str(d.date()))
            ret, msg = self._cmd(cmd)
            if ret != 0:
                raise SSHError
            branch = []
            try:
                for p in msg:
                    bjson = json.loads(p)
                    pr = bjson.get('project', None)
                    if pr != None and (pr.startswith('git/android/vendor/marvell/ose') or
                        pr.startswith('git/android/vendor/marvell/ptk') or
                        pr.startswith('git/qae') or
                        pr.startswith('git/android/shared') or
                        pr.startswith('git/android/tools')):
                        continue
                    br = bjson.get('branch', None)
                    if br != None:
                        branch.append(br)
            except ValueError as e:
                print('Warning: illegal char in gerrit query result')
            branch = list(set(branch))
            with open(gerrit_branch_file, 'w+') as file:
                for br in branch:
                    file.write(br + '\n')
            print('Update branch candidate list done!')

    def _get_project_info(self):
        cmd = 'git remote -v'
        ret, lines = self._cmd(cmd)
        for line in lines:
            line = line.strip()
            if line.endswith('(push)'):
                remote = line.split()
                self.remote = remote[0].strip()
                self.project = remote[1].strip()
                protocol, addr = remote[1].split('//')
                self.protocol = protocol.strip(':')
                if addr.find('@') >= 0:
                    user, addr = addr.split('@')
                    self.user = user
                pos =  addr.index('/')
                self.project = addr[pos:]
                server = addr[0:pos]
                if server.find(':') >= 0:
                    server, port = server.split(':')
                    self.gerrit_port = port
                self.server = server
                break
        if (self.remote == '' or
                self.protocol == '' or
                self.server == '' or
                self.project == ''):
            raise  GitError

    def _get_git_user(self):
        if self.user == '':
            cmd = 'git config --get user.email'
            ret, lines = self._cmd(cmd)
            if ret == 0:
                self.user = lines[0].split('@')[0]
            else:
                print('Please config your git user.email')
                exit(1)

    def _get_commit_ids(self):
        cmd = 'git log --format=%h {}/{}..'.format(self.remote, self.branch)
        ret, msg = self._cmd(cmd)
        if ret == 0:
            self.commit_ids = msg

    def _check_branch_valid(self):
        branch_exist = False
        cmd = 'git branch -a'
        ret, msg = self._cmd(cmd)
        for line in msg:
            line = line.strip().strip('\n')
            if line.endswith(self.branch):
                branch_exist = True
                break
        return branch_exist

    def _check_changeid(self):
        for ci in self.commit_ids:
            cmd = 'git show --format=%b -s {}'.format(ci)
            ret, log = self._cmd(cmd)
            if ' '.join(log).rfind('Change-Id: ') < 0:
                raise ChangeIDError(ci.strip('\n'))
 
    def _check_sign(self):
        for ci in self.commit_ids:
            cmd = 'git show --format=%b -s {}'.format(ci)
            ret, log = self._cmd(cmd)
            if ' '.join(log).rfind('Signed-off-by') < 0:
                raise SignError(ci.strip('\n'))

    def _get_push_cmd(self):
        push_cmd = 'git push {}://{}@{}:{}{} HEAD:refs/for/{}'
        cmd = push_cmd.format(self.protocol, self.user, self.server,
                self.gerrit_port, self.project, self.branch)
        return cmd

    def _set_reviewer(self):
        if self.reviewer != None:
            reviewer_list = self.reviewer.split(',')
            for commit in self.commit_ids:
                for reviewer in reviewer_list:
                    reviewer_cmd = 'ssh {}@{} -p {} gerrit set-reviewers -a {}@{} {}'
                    cmd = reviewer_cmd.format(self.user, self.server, self.gerrit_port,
                            reviewer, self.email, commit)
                    self._cmd(cmd)
    
    def _set_code_review(self):
        if self.review:
            for commit in self.commit_ids:
                review_cmd = 'ssh {}@{} -p {} gerrit review --code-review +1 {}'
                cmd = review_cmd.format(self.user, self.server, self.gerrit_port, commit)
                self._cmd(cmd)

    def _set_code_verify(self):
        if self.verify:
            for commit in self.commit_ids:
                verify_cmd = 'ssh {}@{} -p {} gerrit review --verified +1 {}'
                cmd = verify_cmd.format(self.user, self.server, self.gerrit_port, commit)
                self._cmd(cmd)

    def _set_comment(self):
        if self.comments != None:
            for commit in self.commit_ids:
                comment_cmd = 'ssh {}@{} -p {} gerrit review -m {} {}'
                cmd = comment_cmd.format(self.user, self.server, self.gerrit_port,
                        self.comments, commit)
                self._cmd(cmd)

    def push(self):
        self._parse_option(self.argv)
        self._check_git()
        self._get_project_info()
        self._get_git_user()
        self._update_gerrit_branches()
        if self.branch == '':
            exit(0)
        if not self._check_branch_valid():
            print('Banch not exist, or "git fetch {}" to confirm'.format(self.remote))
            exit(0)
        self._get_commit_ids()
        if len(self.commit_ids) == 1 and self.commit_ids[0] == '':
            print('No new changes for push!')
            exit(0)
        self._check_sign()
        self._check_changeid()
        cmd = self._get_push_cmd()
        print(cmd)
        if sys.version_info[0] == 3:
            confirm = input('Push these commits? [y/n]: ')
        else:
            confirm = raw_input('Push these commits? [y/n]: ')
        if confirm.lower() == 'y' or confirm.lower() == 'yes':
            ret, msg = self._cmd(cmd)
            print(''.join(msg))
            if ret != 0:
                exit(1)
        else:
            print('Abort!!!')
            exit(0)
        self._set_reviewer()
        self._set_code_review()
        self._set_code_verify()
        self._set_comment()
       
if __name__ == '__main__':
    try:
        gerrit = Gerrit(sys.argv)
        gerrit.push()
    except ChangeIDError as e:
        print('{} no Change-ID, get commit-msg hook by'.format(e))
        print('   scp -p -P 29418 shgit.marvell.com:hooks/commit-msg .git/hooks/')
        print('and commit again.')
    except SignError as e:
        print('{} no sign, please add "-a" when do commit.'.format(e))
    except GitError as e:
        print('Not a git')
    except SSHError as e:
        print('Can not access ssh server {}://{}'.format(gerrit.protocol, gerrit.server))
