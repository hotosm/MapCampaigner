import os
import random
import string

SIMPLE_CHARS = string.ascii_letters + string.digits

basedir = os.path.abspath(os.path.dirname(__file__))


def absolute_path(*args):
    """Get an absolute path for a file that is relative to the root.

    :param args: List of path elements.
    :type args: list

    :returns: An absolute path.
    :rtype: str
    """
    return os.path.join(basedir, *args)


def get_random_string(length=24):
    return ''.join(random.choice(SIMPLE_CHARS) for i in range(length))


def ensure_secret_key_file():
    """Checks that secret.py exists in settings dir.

    If not, creates one with a random generated SECRET_KEY setting."""
    secret_path = absolute_path('secret.py')
    if not os.path.exists(secret_path):
        secret_key = get_random_string(
            50)
        with open(secret_path, 'w') as f:
            f.write("SECRET_KEY = " + repr(secret_key) + "\n")


# Import the secret key
ensure_secret_key_file()
