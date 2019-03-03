# pylint: disable=no-member
import threading
import os
import json
from flask import Flask, request, abort, jsonify

# pylint: disable=invalid-name
app = Flask(__name__)


@app.route('/')
# Returns harvester information.
def info():
    return jsonify(app.config['harvest_info'].to_dict())

@app.route('/stop')
# Stops the harvester, but doesn't cause the process to exit.
def stop():
    if 'secret_key' in os.environ and os.environ['secret_key'] != request.args.get('secret_key'):
        abort(401)
    app.logger.debug('Stopping')
    app.config['stop_event'].set()
    return 'Stopping (but not shutting down) ...'


@app.route('/is_stopped')
# Returns True if the harvester is stopped.
def is_stopped():
    if 'secret_key' in os.environ and os.environ['secret_key'] != request.args.get('secret_key'):
        abort(401)
    return json.dumps(app.config['stopped_event'].is_set())


@app.route('/shutdown')
# Stops the harvester and causes the process to exit.
def shutdown():
    if 'secret_key' in os.environ and os.environ['secret_key'] != request.args.get('secret_key'):
        abort(401)
    app.logger.debug('Shutting down')
    app.config['stop_event'].set()
    app.config['shutdown_event'].set()
    return 'Stopping and shutting down...'


# Thread that runs this Flask application.
class ServerThread(threading.Thread):
    def __init__(self, stop_event, stopped_event, shutdown_event, harvest_info):
        threading.Thread.__init__(self)
        self.daemon = True
        app.config['stop_event'] = stop_event
        app.config['stopped_event'] = stopped_event
        app.config['shutdown_event'] = shutdown_event
        app.config['harvest_info'] = harvest_info

    def run(self):
        app.run(host='0.0.0.0', port=80, debug=False)
