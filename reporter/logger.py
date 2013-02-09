import logging
import os


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
    """Set up our logger.

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
    myTempDir = ('/tmp')
    myFilename = os.path.join(myTempDir, 'reporter.log')
    myFileHandler = logging.FileHandler(myFilename)
    myFileHandler.setLevel(myDefaultHanderLevel)
    # create console handler with a higher log level
    myConsoleHandler = logging.StreamHandler()
    myConsoleHandler.setLevel(logging.ERROR)

    try:
        #pylint: disable=F0401
        from raven.handlers.logging import SentryHandler
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
