from flask import Blueprint

campaign_manager = Blueprint(
        'campaign_manager',
        __name__,
        template_folder='templates')

from campaign_manager import views
