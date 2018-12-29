#!/usr/bin/python
#
# An example hook script to verify what is about to be committed.
# Called by "git commit" with no arguments.  The hook should
# exit with non-zero status after issuing an appropriate message if
# it wants to stop the commit.
#
# To enable this hook, rename this file to "pre-commit".
import string
import os
import commands

def increase_version(file_name):
    file = open(file_name, 'r+')
    line = file.read()
    try:
        prefix, num = line.split('=')
        num = num.strip()
        suffix = num[-1]
        if not suffix.isdigit():
            num = num.strip(suffix)
        num = string.atof(num) + 0.01
        version = prefix.strip() + ' = ' + str(num)
        if not suffix.isdigit():
            version += suffix
        file.seek(0)
        file.truncate(0)
        file.write(str(version))
    except ValueError as e:
        pass
    finally:
        file.close()
    (status, HEAD) = commands.getstatusoutput('git rev-parse HEAD')
    if status == 0:
        (status, msg) = commands.getstatusoutput('git commit -a -s --amend -C' + HEAD)
    if status != 0:
        (status, msg) = commands.getstatusoutput('git reset --hard HEAD')

    return status

status = 0
with open('version.def', 'r') as file:
    for line in file:
        version_file = line.strip()
        if os.path.exists(version_file):
            status = increase_version(version_file)
exit(status)
