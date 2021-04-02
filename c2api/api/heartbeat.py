import logging

from flask import request
from flask_restplus import Resource
from c2api.api.api import api
from c2api.api.serializers import heartbeat
from flask import Response
from c2api.api import operations
log = logging.getLogger(__name__)

ns = api.namespace('heartbeat', description='API endpoint for Heartbeat Operations')

@ns.route('')
@api.response(200, 'Heartbeat successfully executed.')
@api.response(400, 'Invalid Heartbeat.')
class Heartbeat(Resource):

    @api.expect(heartbeat)
    def post(self):
        content = request.json
        if content['operation'] is not None:
            if content['operation'] == "heartbeat":
                return operations.perform_heartbeat(content)
            if content['operation'] == "acknowledge":
                return operations.perform_acknowledge(content)
        return Response("{'error':'Invalid heartbeat'}", status=400, mimetype='application/json')