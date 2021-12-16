from os import name
from typing import List, Optional
from dataclasses import field, dataclass

from function_opt import FunctionOpt
from function_ipt import FunctionIpts
from function_interface import FunctionInterface


@dataclass
class Function:
    name: str
    group_name: str
    description: str
    ipts: FunctionIpts
    opts: List[FunctionOpt]
    process_stages: List[str]
    id: Optional[str]=None
    exe_func=None


@dataclass
class FunctionGroup:
    name: str
    functions: List[Function] = field(default_factory=list)

    def add_function(
        self, 
        name: str, description: str, 
        func: FunctionInterface
    ):
        for i in self.functions:
            assert i.name == name, "not allowed same function name under same group"
        self.functions.append(Function(
            name=name, group_name=self.name,
            description=description, 
            ipts=func.ipt_config(),
            opts=func.opt_config(),
            process_stages=func.all_process_stages()))