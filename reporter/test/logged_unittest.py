# -*- coding: utf-8 -*-
"""
    Provides a custom unit test base class which will log to sentry.

    :copyright: (c) 2010 by Tim Sutton
    :license: GPLv3, see LICENSE for more details.
"""
import unittest
import logging
from reporter import setup_logger

setup_logger()
LOGGER = logging.getLogger('osm-reporter')


class LoggedTestCase(unittest.TestCase):
    """A test class that logs to sentry on failure."""
    def failureException(self, msg):
        """Overloaded failure exception that will log to sentry.

        :param msg: String containing a message for the log entry.
        :type msg: str

        :returns: delegates to TestCase and returns the exception generated
            by it.
        :rtype: Exception

        See unittest.TestCase to see what gets raised.
        """
        LOGGER.exception(msg)
        return super(LoggedTestCase, self).failureException(msg)
