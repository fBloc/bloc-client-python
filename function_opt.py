from pydantic import BaseModel

from value_type import ValueType


class FunctionOpt(BaseModel):
    key: str
    description: str
    value_type: ValueType
    is_array: bool
