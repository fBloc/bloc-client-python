import abc
from typing import List

from function_opt import FunctionOpt
from function_ipt import FunctionIpt


class FunctionInterface(metaclass=abc.ABCMeta):
    @classmethod
    def __subclasshook__(cls, subclass):
        return (
            hasattr(subclass, 'all_process_stages') and 
            callable(subclass.all_process_stages) and 
            hasattr(subclass, 'ipt_config') and 
            callable(subclass.ipt_config) and 
            hasattr(subclass, 'opt_config') and 
            callable(subclass.opt_config) or 
            NotImplemented)

    @abc.abstractmethod
    def run(self) -> List[FunctionIpt]:
        raise NotImplementedError

    @abc.abstractmethod
    def ipt_config(self) -> List[FunctionIpt]:
        raise NotImplementedError

    @abc.abstractmethod
    def opt_config(self) -> List[FunctionOpt]:
        raise NotImplementedError

    @abc.abstractmethod
    def all_process_stages(self) -> List[str]:
        raise NotImplementedError