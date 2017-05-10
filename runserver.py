# from reporter import app
from flask import Flask
from reporter import reporter
from campaign_manager import campaign_manager

app = Flask(__name__)
app.register_blueprint(reporter)
app.register_blueprint(campaign_manager)
app.run(debug=True, host='0.0.0.0')
