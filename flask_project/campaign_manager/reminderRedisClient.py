from redis import Redis

r_server = Redis("localhost")  # change localhost to IP


def store_message(id_message, id_sender, reminder, reminder_time, delivered):
    r_server.rpush(id_message, id_sender)
    r_server.rpush(id_message, reminder)
    r_server.r_push(id_message, reminder_time)
    r_server.r_push(id_message, delivered)
    return r_server
