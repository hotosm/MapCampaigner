import sys
import os

ROOT_PROJECT_FOLDER = os.path.dirname(__file__)
path1 = os.path.abspath(os.path.join(ROOT_PROJECT_FOLDER, '..'))
sys.path.append( path1 )
path2 = os.path.abspath(os.path.join(ROOT_PROJECT_FOLDER, '..', 'reporter'))
sys.path.append( path2 )

from reporter.core import app as application
