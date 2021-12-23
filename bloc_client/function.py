from typing import List
from dataclasses import field, dataclass

from bloc_client.function_opt import FunctionOpt
from bloc_client.function_ipt import FunctionIpt
from bloc_client.function_interface import FunctionInterface


@dataclass
class Function:
    id: str = field(init=False)
    name: str
    group_name: str
    description: str
    ipts: List[FunctionIpt]
    opts: List[FunctionOpt]
    process_stages: List[str]
    exe_func: FunctionInterface=field(default=None)

    def json_dict(self):
        return {
            'name': self.name,
            'group_name': self.group_name,
            'description': self.description,
            'ipts': [i.json_dict() for i in self.ipts],
            'opts': [i.json_dict() for i in self.opts],
            'process_stages': self.process_stages
        }


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
        self.functions.append(
            Function(
                name=name, 
                group_name=self.name,
                description=description, 
                ipts=func.ipt_config(),
                opts=func.opt_config(),
                process_stages=func.all_process_stages(),
                exe_func=func
            )
        )
