# coding=utf-8
"""This is the main package for the application.
:copyright: (c) 2013 by Tim Sutton
:license: GPLv3, see LICENSE for more details.
"""

import os
import logging

from flask import Flask


def add_handler_once(logger, handler):
    """A helper to add a handler to a logger, ensuring there are no duplicates.

    Args:
        * logger: logging.logger instance
        * handler: logging.Handler instance to be added. It will not be
            added if an instance of that Handler subclass already exists.

    Returns:
        bool: True if the logging handler was added

    Raises:
        None
    """
    myClassName = handler.__class__.__name__
    for myHandler in logger.handlers:
        if myHandler.__class__.__name__ == myClassName:
            return False

    logger.addHandler(handler)
    return True


def setup_logger():
    """Set up our logger with sentry support.

    Args: None

    Returns: None

    Raises: None
    """
    myLogger = logging.getLogger('osm-reporter')
    myLogger.setLevel(logging.DEBUG)
    myDefaultHanderLevel = logging.DEBUG
    # create formatter that will be added to the handlers
    myFormatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    myTempDir = '/tmp'
    # so e.g. jenkins can override log dir.
    if 'OSM_REPORTER_LOGFILE' in os.environ:
        myFilename = os.environ['OSM_REPORTER_LOGFILE']
    else:
        myFilename = os.path.join(myTempDir, 'reporter.log')
    myFileHandler = logging.FileHandler(myFilename)
    myFileHandler.setLevel(myDefaultHanderLevel)
    # create console handler with a higher log level
    myConsoleHandler = logging.StreamHandler()
    myConsoleHandler.setLevel(logging.ERROR)

    try:
        #pylint: disable=F0401
        from raven.handlers.logging import SentryHandler
        # noinspection PyUnresolvedReferences
        from raven import Client
        #pylint: enable=F0401
        myClient = Client(
            'http://12ef42a1d4394255a2041ac0428e8ef7:'
            '755880e336f54892bc2a65d308019997@sentry.linfiniti.com/6')
        mySentryHandler = SentryHandler(myClient)
        mySentryHandler.setFormatter(myFormatter)
        mySentryHandler.setLevel(logging.ERROR)
        add_handler_once(myLogger, mySentryHandler)
        myLogger.debug('Sentry logging enabled')

    except ImportError:
        myLogger.debug('Sentry logging disabled. Try pip install raven')

    #Set formatters
    myFileHandler.setFormatter(myFormatter)
    myConsoleHandler.setFormatter(myFormatter)

    # add the handlers to the logger
    add_handler_once(myLogger, myFileHandler)
    add_handler_once(myLogger, myConsoleHandler)

setup_logger()
LOGGER = logging.getLogger('osm-reporter')

app = Flask(__name__)
# Don't import actual view methods themselves - see:
# http://flask.pocoo.org/docs/patterns/packages/#larger-applications
# Also views must be imported AFTER app is created above.
# noinspection PyUnresolvedReferences
import reporter.views
