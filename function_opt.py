from dataclasses import dataclass

from value_type import ValueType


@dataclass
class FunctionOpt:
    key: str
    description: str
    value_type: ValueType
    is_array: bool
