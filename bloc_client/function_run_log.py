from os import path
from enum import Enum
from copy import deepcopy
from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass, field

from bloc_client.internal.http_util import sync_post_to_server

LogReportPath = "report_log"


class LogLevel(Enum):
    info = "info"
    warning = "warning"
    error = "error"
    unknown = "unknown"


@dataclass
class FunctionRunMsg:
    level: LogLevel
    msg: str


@dataclass
class LogMsg:
    level: LogLevel
    data: str
    time: datetime=field(default_factory=datetime.now)

    def json_dict(self):
        return {
            "level": self.level.value,
            "date": self.data,
            "time": self.time
        }


@dataclass
class Logger:
    _server_url: str
    name: str
    _msgs: List[LogMsg]=field(default_factory=list)
    _last_upload_time: Optional[datetime]=None

    @staticmethod
    def New(server_url:str, name:str) -> "Logger":
        return Logger(
            _server_url=server_url,
            name=name)
    
    def periodic_pub(self):
        if self._last_upload_time == None:
            self._last_upload_time = datetime.now()
            return
        not_reported_seconds = (datetime.now() - self._last_upload_time).total_seconds()
        if not_reported_seconds >= 10:
            # TODO need lock?
            self._last_upload_time = datetime.now()
            msgs = deepcopy(self._msgs)
            self._msgs[:] = []
            self.upload(msgs)

    def info(self, msg: str):
        self._msgs.append(
            LogMsg(
                level=LogLevel.info,
                data=msg
            )
        )
        self.periodic_pub()

    def warning(self, msg: str):
        self._msgs.append(
            LogMsg(
                level=LogLevel.warning,
                data=msg
            )
        )
        self.periodic_pub()
    
    def error(self, msg: str):
        self._msgs.append(
            LogMsg(
                level=LogLevel.error,
                data=msg
            )
        )
        self.periodic_pub()
    
    def unknown(self, msg: str):
        self._msgs.append(
            LogMsg(
                level=LogLevel.unknown,
                data=msg
            )
        )
        self.periodic_pub()
    
    def add_msg(self, func_run_msg: FunctionRunMsg):
        if func_run_msg.level == LogLevel.info:
            self.info(func_run_msg.msg)
        elif func_run_msg.level == LogLevel.warning:
            self.warning(func_run_msg.msg)
        elif func_run_msg.level == LogLevel.error:
            self.error(func_run_msg.msg)
        else:
            self.unknown(func_run_msg.msg)

    def upload(self, msgs:List[LogMsg]):
        if not msgs: return
        _, err = sync_post_to_server(
            path.join(self._server_url, LogReportPath),
            data={
                "name": self.name,
                "log_data": [i.json_dict() for i in msgs]
            }
        )
        return err

    def force_upload(self):
        self.upload(self._msgs)
