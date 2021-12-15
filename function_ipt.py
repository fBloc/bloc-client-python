from typing import List, Any, Optional
from dataclasses import dataclass

from value_type import ValueType
from select_options import SelectOption
from formcontrol_type import FormControlType

@dataclass
class IptComponent:
    value_type: ValueType
    formcontrol_type: FormControlType
    hint: str
    default_value: Any
    allow_multi: bool
    select_options: Optional[List[SelectOption]]=None
    value: Optional[Any]=None

@dataclass
class FunctionIpt:
    key: str
    display: str
    must: bool
    components: List[IptComponent]
    
FunctionIpts = List[FunctionIpt]