import sys, json
import model
import config
import sync

from flask import Flask
from flask import url_for,redirect, session
from pocket import Pocket, APIError
from log import logger

app = Flask(__name__)
app.debug = config.DEBUG
app.secret_key = config.SECRET

@app.route('/')
def index():
    username = session.get('username')
    access_token = session.get('access_token')
    if username is None or access_token is None:
        return redirect('/auth')
    
    items = model.Item.select().where(model.Item.username == username)
    return json.dumps([item.jsonify() for item in items])

@app.route('/auth')
def auth():
    pocket = Pocket(config.POCKET_CONSUMER_KEY, config.BASE_URL +
            url_for('auth_callback'))
    try:
        code = pocket.get_request_token()
        url = pocket.get_authorize_url(code)
    except APIError as apie:
        return str(apie)
    session.pop('code', None)
    session['code'] = code
    return redirect(url)

@app.route('/auth_callback')
def auth_callback():
    pocket = Pocket(config.POCKET_CONSUMER_KEY)
    code = session['code']
    try:
        resp = pocket.get_access_token(code)
        session.pop('access_token', None)

        username = resp['username']
        token = resp['access_token']

        session['access_token'] = token
        session['username'] = username
        model.User.insert(name = username, token = token).upsert().execute()
        # add async task
        sync.pool.add_task(sync.sync_all_for_user, username, token)
    except APIError as apie:
        return str(apie)
    return session['username'] + " " + session['access_token']

if __name__ == '__main__':
    app.run('0.0.0.0', 9999)
