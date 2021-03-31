import time
from re import I
import sys
from models import ComponentStatus, ConnectionStatus, db ,Heartbeat, AgentInfo, FlowInfo, PendingOperations, AgentClass, Operations, OperationArguments
from flask import Flask, request, jsonify, Response

def create_agent(operation,agent_ident,flow_id,agent_class, content, flow_info_content):
    new_agent_info = AgentInfo(id=agent_ident,agent_class=agent_class,flow_id=flow_id)
    db.session.add(new_agent_info)
    new_heartbeat = Heartbeat(operation=operation,agent_id=agent_ident)
    db.session.add(new_heartbeat)
    if flow_info_content is not None:
        ## we need to go through and add components and queues for this agent.
        queues = flow_info_content.get('queues',{})
        for key,value in queues.items():
            connection = ConnectionStatus(component_uuid=key)
            for comp_key,comp_value in value.items():
                if comp_key == "name":
                    connection.component_name=comp_value
                if comp_key == "size":
                    connection.size=comp_value
                if comp_key == "sizeMax":
                    connection.sizeMax=comp_value
                if comp_key == "dataSize":
                    connection.data=comp_value
                if comp_key == "dataSizeMax":
                    connection.dataMax=comp_value
            connection.component_status="running"
            new_agent_info.connection_statuses.append(connection)
        queues = flow_info_content.get('components',{})
        for key,value in queues.items():
            component = ComponentStatus(component_name=key)
            for comp_key,comp_value in value.items():
                if comp_key == "running":
                    if comp_value is True:
                        component.component_status="running"
                    else:
                        component.component_status="stopped"
                if comp_key == "uuid":
                    component.component_uuid=comp_value
            new_agent_info.component_statuses.append(component)
    db.session.commit()

class Agent:
    def __init__(self,agent_id):
        self.agent_id = agent_id
        agent_info = AgentInfo.query.filter_by(id=self.agent_id).first()           
        self.agent_class = agent_info.agent_class
        self.flow_id = agent_info.flow_id
        self.component_statuses = agent_info.component_statuses
        self.repository_statuses = agent_info.repository_statuses

    def create_flow(self,new_flow_id, flow_info):
        try:
            bucket_id = flow_info['versionedFlowSnapshotURI'].get('bucketId',"")
            registry_url = flow_info['versionedFlowSnapshotURI'].get('registryUrl',"")
            print("creating flow with " + new_flow_id)
            new_flow_info = FlowInfo(flow_id=new_flow_id,bucketId=bucket_id,registry_url=registry_url)
            db.session.add(new_flow_info)
            db.session.commit()
        except:
            e = sys.exc_info()[0]
            print(e)
            raise e
        flow = FlowInfo.query.filter_by(flow_id=new_flow_id).first()
        return flow

    def update_flow(self,new_flow_id,flow_info):
        ## delete the component statuses from the agent info
        pass
        ## delete the queues from flow info
        pass
        ## delete the component info from flow info
        flow = FlowInfo.query.filter_by(flow_id=new_flow_id).first()
        ## only create the flow if it doesn't exist
        if flow is None:
            flow = self.create_flow(new_flow_id,flow_info)
        self.flow_id = new_flow_id
        agent_info = AgentInfo.query.filter_by(id=self.agent_id).first()           
        agent_info.flow_id = self.flow_id
        db.session.commit()
        return flow

class AgentHeartbeat:
    def __init__(self,heartbeat_id,agent_id):
        new_heartbeat = Heartbeat(operation="heartbeat",id=heartbeat_id)
        self.operation_id = new_heartbeat.id
        self.operation = new_heartbeat.operation
        self._agent = Agent(agent_id)

        
    
    def __str__(self):
        resp = dict()
        resp["operation"] = self.operation
        resp["operationId"] = str(self.operation_id)
        pending_operations = PendingOperations.query.filter_by(agent_id=self._agent.agent_id, status="new").all()
        if pending_operations is not None:
            requested_ops = []
            for pending_op in pending_operations:
                op = Operations.query.filter_by(id=pending_op.operation_id).first()
                if op is not None:
                    new_op = dict()
                    new_op["operation"] = op.operand
                    new_op["name"] = op.name
                    new_op["operationId"] = op.id
                    new_op["content"] = dict()
                    for arg in op.operation_arguments:
                        new_op["content"][arg.name] = arg.value
                    requested_ops.append(new_op)
            if len(requested_ops) > 0:
                resp["requested_operations"] = requested_ops
        print(str(resp))
        return jsonify(resp)

def queue_operation(operand, name, args):
    new_operation = Operations(name=name,operand=operand)

    for argkey,argvalue in args.items():
        new_arg = OperationArguments(name=argkey,value=argvalue)
        new_operation.operation_arguments.append(new_arg)
    db.session.add(new_operation)
    db.session.commit()
    return new_operation.id

def has_new_operation(operand,agent_id):
    pending_operations = PendingOperations.query.filter_by(agent_id=agent_id, status="new").all()
    if pending_operations is None:
        return False
    for op in pending_operations:
        pending_operations = Operations.query.filter_by(id=op.operation_id, operand=operand).first()     
        if pending_operations is not None:
            return True
    return False

def assign_operation(operation_id,agent_id):
    new_op = PendingOperations(operation_id=operation_id,agent_id=agent_id,status="new")
    db.session.add(new_op)
    db.session.commit()


def verify_flow(agent_id,flow_id,agent_class):
    ## get the expected class
    flow_class = AgentClass.query.filter_by(agent_class=agent_class).first()
    if flow_class is None:
        return True
    flow = FlowInfo.query.filter_by(flow_id=flow_id).first()
    if flow is None:
        return True

    if flow.flow_id != flow_class.flow_id:
        print("expected " + flow_class.flow_id + " got " + flow.flow_id)
        return False

    return True

def update_flow(agent_id,flow_id):
    ## update the agent id to the flow_id
    if has_new_operation("update",agent_id) is False:
        operand="update"
        name = "configuration"
        arguments = dict()

        flow = FlowInfo.query.filter_by(flow_id=flow_id).first()

        if flow is None:
            return

        arguments['location'] = flow.registry_url
        ## first create an operation
        new_op_id = queue_operation(operand,name,arguments)
        assign_operation(new_op_id,agent_id)
        ## now set it pending for the 

    ## make sure we don't already have an operation pending for this      


def create_class(agent_class,flow_id):
    new_class = AgentClass(agent_class=agent_class,flow_id=flow_id)
    db.session.add(new_class)
    db.session.commit()

def update_agent(operation,agent_ident,flow_id,agent_class, content, flow_info_content):
    agent_info = AgentInfo.query.filter_by(id=agent_ident).first()           
    if agent_info is None:
        create_agent(operation,agent_ident,flow_id,agent_class,content,flow_info_content)
    return Agent(agent_ident)

def update_heartbeat(agent_ident,agent_class, content):
    new_heartbeat = Heartbeat(operation="heartbeat",agent_id=agent_ident,timestamp=time.time()*1000)
    db.session.add(new_heartbeat)
    db.session.commit()
    return AgentHeartbeat(new_heartbeat.id,agent_ident)

def perform_acknowledge(content):
    op_id = content.get("operationId")
    if op_id is None:
        op_id = content.get("identifier","")
    pending_operation = PendingOperations.query.filter_by(id=op_id).first()
    if pending_operation is not None:
        pending_operation.status="finished"
        db.session.commit()
    return Response("{'status':'acknowledged'}", status=200, mimetype='application/json')

def update_status(agent_ident,flow_id,flow_info_content):
    if flow_info_content is not None:
        agent_info = AgentInfo.query.filter_by(id=agent_ident).first()
        ## we need to go through and add components and queues for this agent.
        queues = flow_info_content.get('queues',{})
        for key,value in queues.items():
            connection = ConnectionStatus(component_uuid=key)
            for connection in agent_info.connection_statuses:
                if connection.component_uuid == key:
                    for comp_key,comp_value in value.items():
                        if comp_key == "name":
                            connection.component_name=comp_value
                        if comp_key == "size":
                            connection.size=comp_value
                        if comp_key == "sizeMax":
                            connection.sizeMax=comp_value
                        if comp_key == "dataSize":
                            connection.data=comp_value
                        if comp_key == "dataSizeMax":
                            connection.dataMax=comp_value
         #   new_agent_info.connection_statuses.append(connection)
        queues = flow_info_content.get('components',{})
        for key,value in queues.items():
            for component in agent_info.component_statuses:
                if component.component_uuid == key:
                    for comp_key,comp_value in value.items():
                        if comp_key == "running":
                            if comp_value is True:
                                component.component_status="running"
                            else:
                                component.component_status="stopped"
                        if comp_key == "uuid":
                            component.component_uuid=comp_value
          #  new_agent_info.component_statuses.append(component)
        db.session.commit()

def perform_heartbeat(content):
    if content['agentInfo'] is not None:
        agentInfo = content['agentInfo']
        agent_ident = agentInfo['identifier']
        agent_class = agentInfo['agentClass']
        print("Performing heartbeat for " + agent_ident)
        agent_class_db = AgentClass.query.filter_by(agent_class=agent_class).first()

        flow_id = None
        ## it is possible for flow info to not exist
        if content['flowInfo'] is not None:
            flow_id = content['flowInfo']['flowId']
        
        agent = update_agent(content['operation'],agent_ident,flow_id,agent_class,content['agentInfo'],content['flowInfo'])
        ## check if the flow id has been changed
        
        last_heartbeat = Heartbeat.query.filter_by(agent_id=agent_ident).order_by(Heartbeat.timestamp.desc()).first()

        flow = FlowInfo.query.filter_by(flow_id=flow_id).first()

        if (flow is None):
            ## add the new flow
            flow = agent.update_flow(flow_id,content['flowInfo'])
        
        ## Don't create the class until it is forced on us.
#        if agent_class_db is None:
 #           create_class(agent_class,flow.flow_id)

        if verify_flow(agent_ident,flow_id,agent_class) is False:
            print("Could not verify flow")
            flow_class = AgentClass.query.filter_by(agent_class=agent_class).first()
            if flow_class is not None:
                update_flow(agent_ident,flow_class.flow_id)

        update_status(agent_ident,flow_id,content['flowInfo'])

        print("flow id is %s",flow.flow_id)

        ## update heartbeat
        heartbeat = update_heartbeat(agent_ident,agent_class,content['agentInfo'])
        return heartbeat.__str__()
    else:
        return Response("{'status':'heartbeat'}", status=200, mimetype='application/json')

def verify_class(agentclass):
    agent_info = AgentInfo.query.filter_by(agent_class=agentclass).first()           
    if agent_info is not None:
        return True
    else:
        return False