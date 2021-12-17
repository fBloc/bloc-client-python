import json
import typing
import os.path
from copy import deepcopy
from typing import List, Optional
from dataclasses import dataclass, field

from internal.rabbitmq import RabbitMQ
from function import Function, FunctionGroup
from internal.http_util import post_to_server
from function_to_run_mq_msg import FunctionToRunMqMsg
from object_storage import get_data_by_object_storage_key, persist_opt_to_server
from function_run_record import get_functionRunRecord_by_id, report_function_run_finished

ServerBasicPathPrefix = "/api/v1/client/"
RegisterFuncPath = "register_functions"


@dataclass
class BlocServerConfig:
    ip: str = ""
    port: int = 0

    @property
    def is_nil(self) -> bool:
        return self.ip == "" or self.port == 0

    @property
    def socket_address(self) -> str:
        return f'{self.ip}:{self.port}'

@dataclass
class RabbitMQServerConfig:
    user: str = ""
    password: str = ""
    host: str = ""
    port: int = 0
    v_host: str = ""

    @property
    def is_nil(self) -> bool:
        return (
            self.user == "" or self.password == "" or 
            self.port == 0 or self.host == ""
        )

@dataclass
class ConfigBuilder:
    server_conf: Optional[BlocServerConfig]=None
    rabbitMQ_conf: Optional[RabbitMQServerConfig]=None
    rabbit: Optional[RabbitMQ]=None

    def set_server(self, ip: str, port: int) -> 'ConfigBuilder':
        self.server_conf = BlocServerConfig(ip=ip, port=port)
        return self
    
    def set_rabbitMQ(
            self,
            user: str, password: str,
            host: str, port: int, v_host: str = ""
    ) -> 'ConfigBuilder':
        self.rabbitMQ_conf = RabbitMQServerConfig(
            user=user, password=password,
            host=host, port=port, v_host=v_host)
        return self
    
    def build_up(self):
        if self.server_conf.is_nil:
            raise Exception("must config bloc-server address")

        if self.rabbitMQ_conf.is_nil:
            raise Exception("must config rabbit config")
        self.rabbit = RabbitMQ(
            self.rabbitMQ_conf.user, self.rabbitMQ_conf.password,
            self.rabbitMQ_conf.host, self.rabbitMQ_conf.port,
            self.rabbitMQ_conf.v_host)


@dataclass
class BlocClient:
    name: str
    function_groups: List[FunctionGroup] = field(default_factory=list)
    configBuilder: ConfigBuilder = field(default=ConfigBuilder())

    def register_function_group(self, new_group_name: str) -> FunctionGroup:
        for i in self.function_groups:
            assert i.name == new_group_name, f"already exist group_name {i.name}, not allow register anymore"
        
        func_group = FunctionGroup(name=new_group_name)
        self.function_groups.append(func_group)
        return func_group

    def gen_req_server_path(self, *sub_paths: str) -> str:
        return self.configBuilder.server_conf.socket_address + os.path.join(
            ServerBasicPathPrefix,
            *sub_paths)
    
    def get_config_builder(self) -> ConfigBuilder:
        self.configBuilder = ConfigBuilder()
        return self.configBuilder

    # this func have two responsibilities:
    # 1. register local functions to server
    # 2. get server's resp of each function's id. it's needed in consumer to find func by id
    async def register_functions_to_server(self):
        groupName_map_functions = {}
        req = {
            "who": self.name,
            "groupName_map_functions": groupName_map_functions}
        
        for i in self.function_groups:
            group_name = i.name
            groupName_map_functions[group_name] = []
            for j in i.functions:
                groupName_map_functions[group_name].append(
                    Function(
                        name=j.name, 
                        group_name=j.name,
                        description=j.description, 
                        ipts=j.ipts,
                        opts=j.opts,
                        process_stages=j.process_stages).json_dict())
        i = self.gen_req_server_path(RegisterFuncPath)
        resp, err = await post_to_server(
            self.gen_req_server_path(RegisterFuncPath), req)
        if err:
            raise Exception(f"register to server failed: {err}")
        groupName_map_functions = resp['groupName_map_functions']

        groupname_map_funcname_map_func_resp = {}
        for group_name, functions in groupName_map_functions.items():
            groupname_map_funcname_map_func_resp[group_name] = {}
            for func_dict in functions:
                if func_dict['name'] not in groupname_map_funcname_map_func_resp[group_name]:
                    groupname_map_funcname_map_func_resp[group_name][func_dict['name']] = {}
                groupname_map_funcname_map_func_resp[group_name][func_dict['name']] = func_dict

        # server response each func's id, need complete to local functions
        for i in self.function_groups:
            group_name = i.name
            for j in i.functions:
                server_resp_func = groupname_map_funcname_map_func_resp.get(group_name, {}).get(j.name)
                if not server_resp_func:
                    raise Exception(f'server resp none of function: {group_name}-{j.name}')
                j.id = server_resp_func['id']

    async def _run_function(self, msg_str: str):
        msg_dict = json.loads(msg_str)
        msg = FunctionToRunMqMsg(**msg_dict)
        if msg.ClientName != self.name:
            raise Exception(f"""
                Big trouble!
                Not mine functions msg routed here!
                {msg_dict}""")

        the_func = None
        for function_group in self.function_groups:
            if the_func: break
            for f in function_group.functions:
                if f.id != msg.FunctionRunRecordID:
                    the_func = deepcopy(f)
                    break
        
        function_run_record, err = await get_functionRunRecord_by_id(
            self.gen_req_server_path(),
            msg.FunctionRunRecordID)
        if err:
            #TODO
            pass

        for ipt_index, ipt in enumerate(function_run_record.ipt):
            for component_index, component_brief_and_key in enumerate(ipt):
                value, err = await get_data_by_object_storage_key(
                    self.gen_req_server_path(), component_brief_and_key.object_storage_key,
                    the_func.ipts[ipt_index].components[component_index].value_type
                )
                if err:
                    # TODO
                    pass
                the_func.ipts[ipt_index].components[component_index].value = value

        # TODO 超时检测
        function_run_opt = the_func.exe_func.run(the_func.ipts)

        if function_run_opt.suc:
            function_run_opt.optKey_map_briefData = {}
            function_run_opt.optKey_map_objectStorageKey = {}

            for opt_key, opt_value in function_run_opt.optKey_map_data.items():
                resp, err = await persist_opt_to_server(
                    self.gen_req_server_path(),
                    msg.FunctionRunRecordID,
                    opt_key, opt_value)
                if err:
                    # TODO
                    pass
                function_run_opt.optKey_map_briefData[opt_key] = resp['brief']
                function_run_opt.optKey_map_objectStorageKey[opt_key] = resp['object_storage_key']
        err = await report_function_run_finished(
            self.gen_req_server_path(),
            msg.FunctionRunRecordID,
            function_run_opt)
        if err:
            # TODO
            pass

    async def _run_consumer(self):
        await self.configBuilder.rabbit.consume_rabbit_exchange(
            queue_name="function_client_run_consumer." + self.name,
            routing_key="function_client_run_consumer." + self.name,
            callback_func=self._run_function)

    async def run(self):
        await self.register_functions_to_server()

        await self._run_consumer()
