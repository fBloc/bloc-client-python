from dataclasses import dataclass
from typing import Any

@dataclass
class SelectOption:
    label: str
    value: Any
