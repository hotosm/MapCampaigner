
from flask import request, jsonify, render_template, Response, abort
from campaign_manager import campaign_manager


@campaign_manager.route('/')
def home():
    """Home page view.

    On this page a map and the report will be shown.
    """
    context = dict(
        testing='hello'
    )
    # noinspection PyUnresolvedReferences
    return render_template('index.html', **context)
