__author__ = 'Irwan Fathurrahman <irwan@kartoza.com>'
__date__ = '16/05/17'

import datetime
import os
import subprocess
from subprocess import call

file_path = os.path.dirname(os.path.abspath(__file__))
git_folder = os.path.join(
    file_path, os.pardir)


def git_pull():
    """ Pulling git.
    """
    os.chdir(git_folder)
    call(["git", "pull", "https://github.com/kartoza/osm-reporter.git"])


def git_add():
    """ Add new files to git git.
    """
    os.chdir(git_folder)
    call(["git", "add", "-A"])


def git_commit():
    """ Add new files to git git.
    """
    os.chdir(git_folder)
    username = subprocess.check_output(
        ['git', 'config', '--global', 'user.name']).decode("utf-8")
    username = username.replace('\n', '')
    now_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    call(["git", "commit", "-m", "%s - %s" % (username, now_date)])


def git_push():
    """ Push commit
    """
    os.chdir(git_folder)
    branch = subprocess.check_output(
        ['git', 'rev-parse', '--abbrev-ref', 'HEAD']).decode("utf-8")
    call("git push origin %s" % branch, shell=True)


def save_with_git():
    """ Saving files with git.

    # 1. pull
    # 2. add
    # 3. commit
    # 4. push
    """
    git_pull()
    git_add()
    git_commit()
    git_push()
