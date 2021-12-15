from os import name
from typing import List, Optional

from pydantic import BaseModel

from function_opt import FunctionOpt
from function_ipt import FunctionIpts
from function_interface import FunctionInterface


class Function(BaseModel):
    id: Optional[str]=None
    name: str
    group_name: str
    description: str
    ipts: FunctionIpts
    opts: List[FunctionOpt]
    process_stages: List[str]
    exe_func: Optional[FunctionInterface]=None


class FunctionGroup(BaseModel):
    name: str
    functions: List[Function]=[]

    def add_function(self, 
        name: str, description: str, 
        func: FunctionInterface
    ):
        for i in self.functions:
            assert i.name == name, "not allowed same function name under same group"
        self.functions.append(Function(
            name=name, group_nam=self.name,
            description=description, 
            ipts=func.ipt_config(),
            opts=func.opt_config(),
            process_stages=func.all_process_stages()))
