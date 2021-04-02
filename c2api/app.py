import platform
import base64
import logging.config
import time
from flask import Flask, request, jsonify, Blueprint
from flask_sqlalchemy import SQLAlchemy
import os
from flask import Response
from flask import current_app
from c2api.api.api import api
app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
from c2api.models import db ,Heartbeat, AgentInfo, FlowInfo, AgentClass,HostedFlows
import c2api.api.operations as operations
from c2api.api.heartbeat import ns as heartbeat_namespace
from c2api.api.query import ns as query_namespace
from c2api.api.update import ns as update_namespace
from flask_restplus import Api
from sqlalchemy.orm.exc import NoResultFound
import traceback
from c2api.config import current_config


logging_conf_path = os.path.normpath(os.path.join(os.path.dirname(__file__), './log.conf'))
logging.config.fileConfig(logging_conf_path)
log = logging.getLogger(__name__)

@app.route('/init')
def initdb():
    db.create_all()
    return "Initialized!"



    
def initialize_app(flask_app):
    blueprint = Blueprint('api', __name__, url_prefix='/api')
    api.init_app(blueprint)
    api.add_namespace(heartbeat_namespace)
    api.add_namespace(query_namespace)
    api.add_namespace(update_namespace)
    flask_app.register_blueprint(blueprint)
    db.init_app(flask_app)
    current_config.MAX_HEARTBEAT = app.config['MAX_HEARTBEAT']
    current_config.UPLOAD_FOLDER = app.config['UPLOAD_FOLDER']
    #db.create_all()

def main():
    initialize_app(app)
    log.info('>>>>> Starting development server at http://{}/api/ <<<<<'.format(platform.node()))
    app.run(host='0.0.0.0', port=5000, debug=app.config['DEBUG'])


if __name__ == "__main__":
    print("entering main")
    main()