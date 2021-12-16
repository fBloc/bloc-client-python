from dataclasses import dataclass
from typing import Any

@dataclass
class SelectOption:
    label: str
    value: Any

    def json_dict(self):
        return {
            'label': self.label,
            'value': self.value
        }
