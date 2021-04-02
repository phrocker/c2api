
from flask_restplus import fields
from c2api.api.api import api


connection = api.model('Connection', {
    'component_name': fields.String(required=True, description='Name of the connection'),
    'component_uuid': fields.String(required=True, description='Connection UUID'),
    'size': fields.Integer(required=True, description='Connection size ( count of flow files in the queue )'),
    'sizeMax': fields.Integer(required=True, description='Connection maximuim size'),
    'data': fields.Integer(required=True, description='Size of data in the queue'),
    'dataMax': fields.Integer(required = True, description='Maximum allowed size of data in the queue'),
})

connections = api.model('Connections', {
    'connections': fields.List(fields.Nested(connection))
})
component = api.model('Component', {
    'component_name': fields.String(required=True, description='Name of the component'),
    'component_uuid': fields.String(required=True, description='Component UUID'),
    'component_status': fields.String(required = True, description='Component Status'),
})

heartbeat = api.model('Heartbeat', {
    'operation': fields.String(required=False, description='Type of operation to perform'),
    'agent_id': fields.String(required=True, description='Agent ID'),
    'timestamp': fields.Integer(required=True, description='Timestamp'),
})

last_heard_heartbeat = api.model('Last Heard', {
    'agent_id': fields.String(required=True, description='Agent ID'),
    'timestamp': fields.Integer(required=True, description='Timestamp'),
})

status = api.model('Operation Status', {
    'status': fields.String(required=True, description='Operation Status'),
    'identifier': fields.String(required=False, description='Operation ID, if one is created'),
    'error': fields.String(required=False, description='Error details if an error occurred')
})

flowinfo = api.model('FlowInfo', {
    'flowId': fields.String(required=True, description='Flow Identifier'),
    'registryUrl': fields.String(required=False, description='Registry URL agents will probe for the flow'),
    'buicketId': fields.String(required=False, description='Bucket ID')
})