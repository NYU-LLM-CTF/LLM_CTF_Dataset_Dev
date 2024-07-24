from CTFd.models import db, WrongKeys, Pages, Config
from CTFd import mail

from urlparse import urlparse, urljoin
from functools import wraps
from flask import current_app as app, g, request, redirect, url_for, session
from flask.ext.mail import Message
from socket import inet_aton, inet_ntoa
from struct import unpack, pack

import time
import datetime
import hashlib
import digitalocean
import shutil


def init_utils(app):
    app.jinja_env.filters['unix_time'] = unix_time
    app.jinja_env.filters['unix_time_millis'] = unix_time_millis
    app.jinja_env.filters['long2ip'] = long2ip
    app.jinja_env.globals.update(pages=pages)
    app.jinja_env.globals.update(can_register=can_register)
    app.jinja_env.globals.update(mailserver=mailserver)


def pages():
    pages = Pages.query.filter(Pages.route!="index").all()
    return pages


def authed():
    return bool(session.get('id', False))


def is_setup():
    setup = Config.query.filter_by(key='setup').first()
    if setup:
        return setup.value
    else:
        return False


def is_admin():
    if authed():
        return session['admin']
    else:
        return False


def can_register():
    config = Config.query.filter_by(key='prevent_registration').first()
    if config:
        return config.value != '1'
    else:
        return True


def admins_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('admin', None) is None:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def ctftime():
    """ Checks whether it's CTF time or not. """

    start = Config.query.filter_by(key="start").first().value
    end = Config.query.filter_by(key="end").first().value

    if start:
        start = int(start)
    if end:
        end = int(end)

    if start and end:
        if start < time.time() and time.time() < end: 
            # Within the two time bounds
            return True

    if start < time.time() and end is None: 
        # CTF starts on a date but never ends
        return True

    if start is None and time.time() < end: 
        # CTF started but ends at a date
        return True

    if start is None and end is None:
        # CTF has no time requirements
        return True

    return False


def can_view_challenges():
    config = Config.query.filter_by(key="view_challenges_unregistered").first()
    if config:
        return authed() or config.value == '1'
    else:
        return authed()


def unix_time(dt):
    epoch = datetime.datetime.utcfromtimestamp(0)
    delta = dt - epoch
    return int(delta.total_seconds())


def unix_time_millis(dt):
    return unix_time(dt) * 1000


def long2ip(ip_int):
    return inet_ntoa(pack('!I', ip_int))


def ip2long(ip):
    return unpack('!I', inet_aton(ip))[0]


def get_kpm(teamid): # keys per minute
    one_min_ago = datetime.datetime.utcnow() + datetime.timedelta(minutes=-1)
    return len(db.session.query(WrongKeys).filter(WrongKeys.team == teamid, WrongKeys.date >= one_min_ago).all())


def get_config(key):
    config = Config.query.filter_by(key=key).first()
    if config:
        return config.value
    else:
        return None


def set_config(key, value):
    config = Config.query.filter_by(key=key).first()
    if config:
        config.value = value
    else:
        config = Config(key, value)
        db.session.add(config)
        db.session.commit()
        return config


def mailserver():
    if app.config['MAIL_SERVER'] and app.config['MAIL_PORT'] and app.config['ADMINS']:
        return True
    return False


def sendmail(addr, text):
    try:
        msg = Message("Message from {0}".format(app.config['CTF_NAME']), sender = app.config['ADMINS'][0], recipients = [addr])
        msg.body = text
        mail.send(msg)
        return True
    except:
        return False


def rmdir(dir):
    shutil.rmtree(dir, ignore_errors=True)

def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


def sha512(string):
    return hashlib.sha512(string).hexdigest()


def get_digitalocean():
    token = get_config('do_api_key')
    if token:
        return digitalocean.Manager(token=token)
    else:
        return False