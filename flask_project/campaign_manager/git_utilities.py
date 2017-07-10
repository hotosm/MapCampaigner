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
    call(
        ["git",
         "pull",
         "git@github.com:hotosm/field-campaigner.git",
         "develop"]
    )


def git_add():
    """ Add new files to git git.
    """
    os.chdir(git_folder)
    call(["git", "add", "-A"])


def git_commit(commit_message=''):
    """ Add new files to git git.

    :param commit_name: Commit name
    :type commit_name: str
    """
    os.chdir(git_folder)
    if not commit_message:
        username = subprocess.check_output(
            ['git', 'config', '--global', 'user.name']).decode("utf-8")
        username = username.replace('\n', '')
        now_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        commit_message = "%s - %s" % (username, now_date)

    call(["git", "commit", "-m", commit_message])


def git_push():
    """ Push commit
    """
    os.chdir(git_folder)
    branch = subprocess.check_output(
        ['git', 'rev-parse', '--abbrev-ref', 'HEAD']).decode("utf-8")
    call("git push origin %s" % branch, shell=True)


def save_with_git(commit_message=''):
    """ Saving files with git.
    # 1. pull
    # 2. add
    # 3. commit
    # 4. push

    :param commit_message: commit_message
    :type commit_message: str
    """
    git_pull()
    git_add()
    git_commit(commit_message)
    git_push()
