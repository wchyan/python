#!/usr/bin/python

from __future__ import unicode_literals
import subprocess
from optparse import OptionParser
import sys
import json
import time
import os
import os.path
import datetime

# 1. Init version
#    Tony Teng
# 2. Add ChangeID check, get user name from git user.email,
#    Weichuan Yan, 2011-01-06
# 3. Support parameters to set reviewers and review status,
#    Carton He
# 4. Upgrade to Python version, fix the git server change
#    relate issues, Weichuan Yan, 2015-07-16

class ChangeIDError(Exception):
    pass

class SignError(Exception):
    pass

class GitError(Exception):
    pass

class SSHError(Exception):
    pass

class Gerrit():
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

    def _cmd(self, cmd):
        msg = []
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        while p.poll()==None:
            line = p.stdout.readline()
            msg.append(line)
        p.wait()
        return (p.returncode, msg)

    def _check_git(self):
        cmd = 'git status'
        ret, lines = self._cmd(cmd)
        if ret != 0:
            raise GitError

    def _update_gerrit_branches(self):
        delta = datetime.timedelta(days=31)
        gerrit_branch_file = os.path.expanduser('~/.gerrit')
        if os.path.exists(gerrit_branch_file):
            mtime = os.path.getmtime(gerrit_branch_file)
            d1 = datetime.datetime.fromtimestamp(mtime)  
            d2 = datetime.datetime.now()
            delta = d2 - d1
        if delta.days <= 30:
            return

        if not os.path.exists(gerrit_branch_file) or delta.days > 30:
            query_cmd = 'gerrit query --format=JSON  age:month status:merged'
            cmd = 'ssh {}@{} -p {} {}'.format(self.user, self.server, self.gerrit_port, query_cmd)
            ret, msg = self._cmd(cmd)
            if ret != 0:
                raise SSHError

            branch = []
            for p in msg:
                bjson = json.loads(p)
                pr = bjson.get('project', None)
                if pr != None and (pr.startswith('git/android/vendor/marvell/ose') or
                    pr.startswith('git/android/vendor/marvell/ptk') or
                    pr.startswith('git/qae') or
                    pr.startswith('git/android/tools')):
                    continue
                br = bjson.get('branch', None)
                if br != None:
                    branch.append(br)
            branch = list(set(branch))
            with open(gerrit_branch_file, 'w+') as file:
                for br in branch:
                    file.write(br + '\n')

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
        if options.user != '':
            self.user = options.user
        if options.email != '':
            self.email = options.email
        if len(args) != 1:
            parser.print_help()
            parser.exit()
        self.branch = args[0]

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

    def _get_git_user(self):
        if self.user == '':
            cmd = 'git config --get user.email'
            ret, lines = self._cmd(cmd)
            if ret == 0:
                self.user = lines[0].split('@')[0]

    def _get_commit_ids(self):
        cmd = 'git log --format=%h {}/{}..'.format(self.remote, self.branch)
        ret, msg = self._cmd(cmd)
        if ret == 0:
            self.commit_ids = msg

    def _check_changeid(self):
        for ci in self.commit_ids:
            cmd = 'git show --format=%b -s {}'.format(ci)
            ret, log = self._cmd(cmd)
            if ' '.join(log).rfind('Change-Id: ') < 0:
                raise ChangeIDError
 
    def _check_sign(self):
        for ci in self.commit_ids:
            cmd = 'git show --format=%b -s {}'.format(ci)
            ret, log = self._cmd(cmd)
            if ' '.join(log).rfind('Signed-off-by') < 0:
                raise SignError

    def _get_push_cmd(self):
        cmd = 'git push {}://{}@{}:{}{} HEAD:refs/for/{}'.format(self.protocol,
                self.user, self.server, self.gerrit_port, self.project, self.branch)
        return cmd

    def _set_reviewer(self):
        if self.reviewer != None:
            reviewer_list = self.reviewer.split(',')
            for commit in self.commit_ids:
                for reviewer in reviewer_list:
                    cmd = "ssh {}@{} -p {} gerrit set-reviewers -a {}@{} {}".format(self.user,
                            self.server, self.gerrit_port, reviewer, self.email, commit)
                    self._cmd(cmd)
    
    def _set_code_review(self):
        if self.review:
            for commit in self.commit_ids:
                cmd = "ssh {}@{} -p {} gerrit review --code-review +1 {}".format(self.user,
                        self.server, self.gerrit_port, commit)
                self._cmd(cmd)

    def _set_code_verify(self):
        if self.verify:
            for commit in self.commit_ids:
                cmd = "ssh {}@{} -p {} gerrit review --verified +1 {}".format(self.user,
                        self.server, self.gerrit_port, commit)
                self._cmd(cmd)

    def _set_comment(self):
        if self.comments != None:
            for commit in self.commit_ids:
                cmd = "ssh {}@{} -p {} gerrit review -m {} {}".format(self.user,
                        self.server, self.gerrit_port, self.comments, commit)
                self._cmd(cmd)

    def push(self):
        self._parse_option(self.argv)
        self._check_git()
        self._get_project_info()
        self._get_git_user()
        self._update_gerrit_branches()
        self._get_commit_ids()
        gerrit._check_sign()
        gerrit._check_changeid()
        cmd = self._get_push_cmd()
        print cmd
        confirm = raw_input('Push these commits? [y/n]: ')
        if confirm.lower() == 'y' or confirm.lower() == 'yes':
            ret, msg = self._cmd(cmd)
            print ''.join(msg)
            if ret != 0:
                exit(1)
        else:
            print 'Abort!!!'
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
        print '''No Change-ID, get commit-msg hook by \n   "scp -p -P 29418 shgit.marvell.com:hooks/commit-msg .git/hooks/"\nand commit again.'''
    except SignError as e:
        print '''No sign, please add '-a' when do commit.'''
    except GitError as e:
        print '''Not a git'''
    except SSHError as e:
        print '''Can't access ssh server %s://%s ''' %  (gerrit.protocol, gerrit.server)
