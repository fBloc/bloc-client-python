from pydantic import BaseModel
from typing import List, Any

from value_type import ValueType
from select_options import SelectOption
from formcontrol_type import FormControlType


class IptComponent(BaseModel):
    value_type: ValueType
    formcontrol_type: FormControlType
    hint: str
    default_value: Any
    allow_multi: bool
    select_options: List[SelectOption]


class FunctionIpt(BaseModel):
    key: str
    display: str
    must: bool
    Components: List[IptComponent]


FunctionIpts = List[FunctionIpt]
