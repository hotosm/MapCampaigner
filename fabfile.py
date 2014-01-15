#!/bin/python
# coding=utf-8
"""Fabfile for changelog app."""
# ~/fabfile.py
# A Fabric file for carrying out various administrative tasks.
# Tim Sutton, Jan 2013

# To use this script make sure you have fabric and fabtools.
# pip install fabric fabtools

import os
import getpass

from fabric.api import task, fastprint, cd, run
from fabric.contrib.project import rsync_project
from fabric.colors import red, blue
from fabtools import require

# Don't remove even though its unused
# noinspection PyUnresolvedReferences
from fabtools.vagrant import vagrant

from fabgis.django import setup_apache
from fabgis.git import update_git_checkout
from fabgis.virtualenv import setup_venv
from fabgis.common import setup_env, show_environment


def get_vars():
    """Helper method to get standard deployment vars.

    :returns: A tuple containing the following:
        * base_path: Workspace dir e.g. ``/home/foo/python``
        * code_path: Project dir e.g. ``/home/foo/python/osm-reporter``
        * git_url: Url for git checkout - use http for read only checkout
        * repo_alias: Name of checkout folder e.g. ``osm-reporter``
        * site_name: Name for the web site e.g. ``osm-reporter``

    :rtype: tuple
    """
    setup_env()
    site_name = 'osm'
    base_path = '/home/web/'
    git_url = 'http://github.com/timlinux/osm-reporter.git'
    repo_alias = 'osm-reporter'
    code_path = os.path.abspath(os.path.join(base_path, repo_alias))
    return base_path, code_path, git_url, repo_alias, site_name


@task
def update_venv(code_path):
    """Update the virtual environment to ensure it has node etc. installed.

    :param code_path: Directory in which project is located.
    :type code_path: str

    e.g.::

        fab -H localhost update_venv:/home/timlinux/dev/python/osm-reporter
    """
    setup_venv(code_path, requirements_file='requirements.txt')


@task
def update_apache(code_path):
    """Update the apache configuration prompting for github account info.

    .. note:: The config file is taken from the local system.

    :param code_path: Usually '/home/web/<site_name>'

    """
    domain = 'changelog.linfiniti.com'
    setup_apache(
        site_name='osm-reporter',
        code_path=code_path,
        domain=domain)


@task
def deploy():
    """Initialise or update the git clone - you can safely rerun this.

    e.g. to update the server

    fab -H <host> deploy

    """
    # Ensure we have a mailserver setup for our domain
    # Note that you may have problems if you intend to run more than one
    # site from the same server
    setup_env()
    show_environment()
    base_path, code_path, git_url, repo_alias, site_name = get_vars()

    fastprint('Checking out %s to %s as %s' % (git_url, base_path, repo_alias))
    update_git_checkout(base_path, git_url, repo_alias)
    require.postfix.server(site_name)
    update_apache(code_path)
    require.deb.package('python-dev')
    update_venv(code_path)
    fastprint('*******************************************\n')
    fastprint(' Setup completed.')
    fastprint('*******************************************\n')


@task
def freshen():
    """Freshen the server with latest git copy and touch wsgi.

    .. note:: Preferred normal way of doing this is rather to use the
        sync_project_to_server task and not to checkout from git.

    """
    base_path, code_path, git_url, repo_alias, site_name = get_vars()
    git_url = 'http://github.com/timlinux/osm-reporter.git'
    update_git_checkout(base_path, git_url, repo_alias)
    with cd(code_path):
        run('touch apache/osm-reporter.wsgi')

    fastprint('*******************************************\n')
    fastprint(red(' Don\'t forget set ALLOWED_HOSTS in \n'))
    fastprint(' django_project/core/settings/prod.py\n')
    fastprint(' to the domain name for the site.\n')
    fastprint('*******************************************\n')



@task
def sync_project_to_server():
    """Synchronize project with webserver ignoring venv and sqlite db..
    This is a handy way to get your secret key to the server too...

    """
    base_path, code_path, git_url, repo_alias, site_name = get_vars()
    update_venv(code_path)
    #noinspection PyArgumentEqualDefault
    rsync_project(
        base_path,
        delete=False,
        exclude=[
            '*.pyc',
            '.git',
            '*.dmp',
            '.DS_Store',
            'osm-reporter.db',
            'venv',
            'django_project/static'])
    with cd(code_path):
        run('touch apache/osm-reporter.wsgi')
    fastprint(blue(
        'Your server is now in synchronised to your local project\n'))




