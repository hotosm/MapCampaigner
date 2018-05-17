import atexit
import json

from flask import render_template, jsonify, request, flash
from flask import session as session_var
from flask_mail import Message
from sqlalchemy import and_, or_
from flask_socketio import send
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from flask_debugtoolbar_lineprofilerpanel.profile import line_profile

from campaign_manager import campaign_manager
from campaign_manager.campaign_serializer import (
    get_campaign_functions,
    get_campaign_geometry,
    map_provider
)
from campaign_manager.views import abort
from campaign_manager.models.models import (
    Campaign,
    User,
    Reminder,
    Chat,
    Recipient,
    session
)
from app_sockets import socketio, osm_app, mail
from flask_celery import make_celery

try:
    from secret import OAUTH_CONSUMER_KEY, OAUTH_SECRET
except ImportError:
    OAUTH_CONSUMER_KEY = ''
    OAUTH_SECRET = ''

celery = make_celery(osm_app)


@line_profile
def serializer_chat(chats):
    """ Serializes the chat object.
    :param: chat objects.
    :type: dict
    :rparam: serialized chat.
    :rtype: dict
    """
    chat_dict = {}
    i = 0
    for chat in chats:
        i += 1
        chat_thread = {}
        chat_thread['message'] = chat.message
        chat_thread['sender'] = chat.sender.osm_user_id
        chat_thread['receiver'] = chat.reciever.osm_user_id
        chat_thread['send_time'] = chat.send_time
        chat_dict['chat' + str(i)] = chat_thread
    return chat_dict


@line_profile
def serializer_remider(reminder):
    """ Serializes the reminder object.
    :param: reminder object.
    :type: dict
    :rparam: serialized reminder.
    :rtype: dict
    """
    reminder_dict = {}
    reminder_dict['message'] = reminder.message
    reminder_dict['sender'] = reminder.sender.email
    reminder_dict['recipients'] = []
    for recipient in reminder.recipients:
        if recipient.user.email != '':
            reminder_dict['recipients'].append(recipient.user.email)
    return reminder_dict


@campaign_manager.route('/add_osm_user', methods=['POST'])
@line_profile
def add_osm_user():
    """Adds a new user to DB.
    :return: confirmation of new user registeration.
    :rtpye: Status code
    """
    session_var['username'] = request.json['username']
    osm_user = User().get_by_osm_id(request.json['username'])
    if osm_user is None:
        new_user = User(osm_user_id=request.json['username'], email='')
        new_user.create()
    return (
        json.dumps({'success': True}),
        200,
        {'ContentType': 'application/json'}
        )


@socketio.on('message')
@line_profile
def save_campaign_chat(msg_obj):
    """ Creates new chat object in DB.
    :param: dict data containing chat details.
    :type: socket object
    :return: message object.
    :rtype: socket
    """
    campaign = Campaign().get_by_uuid(msg_obj['uuid'])
    sender = User().get_by_osm_id(msg_obj['sender'])
    receiver = User().get_by_osm_id(msg_obj['receiver'])
    chat = Chat(
        campaign_id=campaign.id,
        sender_id=sender.id,
        receiver_id=receiver.id,
        message=msg_obj['message'],
        send_time=datetime.now())
    chat.create()
    send_obj = []
    context = {}
    context['message'] = msg_obj['message']
    context['sender'] = msg_obj['sender']
    context['type'] = msg_obj['type']
    send_obj.append(context)
    send(send_obj, broadcast=True)


@campaign_manager.route('/get_chat/<sender>/<receiver>')
@line_profile
def get_campaign_chat(sender, receiver):
    """ Returns serialized chat messages.
    :param1: message sender id.
    :type: str
    :param2: message receiver id.
    type: str
    :return: serailzed chat with provided participants.
    :rtype: dict 
    """
    sender = User().get_by_osm_id(sender)
    receiver = User().get_by_osm_id(receiver)
    chat = Chat().get_participant_chat(sender, receiver)
    chat = serializer_chat(chat)
    return jsonify(chat)


@campaign_manager.route('/admin/<uuid>', methods=['GET'])
@line_profile
def admin_view(uuid):
    """ Gets the admin view."""
    session_var.pop('_flashes', None)
    context = {}
    campaign = Campaign().get_by_uuid(uuid)
    context['campaign'] = campaign
    context['oauth_consumer_key'] = OAUTH_CONSUMER_KEY
    context['oauth_secret'] = OAUTH_SECRET
    context[uuid] = uuid
    teams = []
    for boundary in campaign.task_boundaries:
        teams.append(boundary.team)
    context['teams'] = teams
    # Start date
    try:
        start_date = campaign.start_date
        context['start_date'] = start_date
    except TypeError:
        context['start_date'] = '-'
    date = datetime.now().date()
    if campaign.start_date <= date and date <= campaign.end_date:
        context['current_status'] = 'running'
    # End date
    try:
        end_date = campaign.end_date
        context['end_date'] = end_date
    except TypeError:
        context['end_date'] = end_date
    # Participant
    context['participants'] = len(campaign.users)
    # Admin
    context['admin'] = session_var['username']
    return render_template('admin_view.html', **context)


@campaign_manager.route('/add_reminder', methods=['POST'])
@line_profile
def add_reminder():
    """ Adds a new reminder to the DB.
    returns: confirmation message.
    """
    from flask import url_for, redirect

    data = request.form
    try:
        campaign = Campaign().get_by_uuid(data['uuid'])
        sender = User().get_by_osm_id(session_var['username'])
        reminder = Reminder(
            message=data['reminder-message'],
            time=data['reminder-time'],
            campaign_id=campaign.id,
            sender_id=sender.id)
        reminder.create()

        for manager in campaign.users:
            recipient = Recipient(
                user_id=manager.id)
            session.add(recipient)
            session.commit()
            reminder.recipients.append(recipient)

        for task_boundary in campaign.task_boundaries:
            team = task_boundary.team
            for member in team.users:
                recipient = Recipient(
                    user_id=member.id)
                session.add(recipient)
                session.commit()
                reminder.recipients.add(recipient)
        session.commit()
        check_remind_time()
        flash("Reminder Created.")
        return redirect(
            url_for(
                'campaign_manager.admin_view',
                uuid=data['uuid'])
            )
    except Exception as e:
        flash("Unable to create reminder.")
        return redirect(
            url_for(
                'campaign_manager.admin_view',
                uuid=data['uuid'])
            )


@celery.task()
def dispatch_reminder(reminder):
    """ Dispatches reminder mail.
    """
    msg = Message(
        reminder['message'],
        sender=reminder['sender'],
        recipients=reminder['recipients'])
    mail.send(msg)


def check_remind_time():
    """ Checks the time to dispatch a reminder.
    """
    import datetime

    reminders = Reminder().get_all()
    for reminder in reminders:
        now = datetime.datetime.now()
        time_dispatch = reminder.time - datetime.timedelta(minutes=10)
        if (
            now <= reminder.time and
            now >= time_dispatch and not
            reminder.is_delivered
        ):
            reminder.is_delivered = True
            session.commit()
            reminder = serializer_remider(reminder)
            dispatch_reminder.delay(reminder)
        else:
            print("Not to dispatched now")


scheduler = BackgroundScheduler()
scheduler.start()
scheduler.add_job(
    func=check_remind_time,
    trigger=IntervalTrigger(seconds=5 * 60),
    id='reminder_job',
    name='checks the reminders to be dispatched every 5 min',
    replace_existing=True)

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())
