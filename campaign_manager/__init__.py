from flask import Blueprint

campaign_manager = Blueprint(
        'campaign_manager',
        __name__,
        template_folder='templates',
        static_folder='static', static_url_path='/static/campaign')

from campaign_manager import views
