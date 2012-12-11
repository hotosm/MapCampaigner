# -*- coding:utf-8 -*-

import os
import re

# import default
from config.default import *

try:
    user_settings = __import__(
        os.environ["REPORTER_CONFIG_MODULE"],
        fromlist=["REPORTER_CONFIG_MODULE"]
    )
except KeyError:
    # Don't fail to keep local config optional
    user_settings = {}

# Override with user ones
for attr in dir(user_settings):
    if re.search('^[a-zA-Z]', attr):
        globals()[attr] = getattr(user_settings, attr)
