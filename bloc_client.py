import os.path
from typing import List, Optional
from collections import defaultdict
from dataclasses import dataclass, field

from internal.http_util import post_to_server
from function import Function, FunctionGroup
from internal.rabbitmq import RabbitMQ

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
        return os.path.join(
            self.configBuilder.server_conf.socket_address,
            ServerBasicPathPrefix,
            *sub_paths)
    
    def get_config_builder(self) -> ConfigBuilder:
        self.configBuilder = ConfigBuilder()
        return self.configBuilder

    # this func have two responsibilities:
    # 1. register local functions to server
    # 2. get server's resp of each function's id. it's needed in consumer to find func by id
    async def register_functions_to_server(self):
        groupname_map_funcname_map_func_req = defaultdict(lambda: defaultdict(lambda: []))
        req = {
            "who": self.name,
            "groupName_map_functionName_map_function": groupname_map_funcname_map_func_req}
        
        for i in self.function_groups:
            group_name = i.name
            for j in i.functions:
                groupname_map_funcname_map_func_req[group_name][j.name].append(
                    Function(
                        name=j.name, 
                        group_name=j.name,
                        description=j.description, 
                        ipts=j.ipts,
                        opts=j.opts,
                        process_stages=j.process_stages))
        groupname_map_funcname_map_func_resp, err = await post_to_server(
            self.gen_req_server_path(RegisterFuncPath), req)
        if err:
            raise Exception(f"register to server failed: {err}")

        # server response each func's id, need complete to local functions
        for i in self.function_groups:
            group_name = i.name
            for j in i.functions:
                server_resp_func = groupname_map_funcname_map_func_resp.get(group_name, {}).get(j.name)
                if not server_resp_func:
                    raise Exception(f'server resp none of function: {group_name}-{j.name}')
                assert isinstance(server_resp_func, Function), ""
                j.id = server_resp_func.id

    @staticmethod
    async def _run_function(function_id: str):
        print(f"received function to run: {function_id}")
        pass

    async def _run_consumer(self):
        await self.configBuilder.rabbit.consume_rabbit_exchange(
            queue_name="function_client_run_consumer." + self.name,
            routing_key="function_client_run_consumer." + self.name,
            callback_func=self._run_function)

    async def run(self):
        await self.register_functions_to_server()
