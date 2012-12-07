import sys
import os

ROOT_PROJECT_FOLDER = os.path.dirname(__file__)
path1 = os.path.abspath(os.path.join(ROOT_PROJECT_FOLDER, '..'))
sys.path.append( path1 )

from reporter.reporter import app as application
