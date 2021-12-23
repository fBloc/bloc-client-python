from typing import Any, Optional
from multiprocessing import Queue

from bloc_client.function_run_log import LogLevel
from bloc_client.function_run_opt import FunctionRunOpt
from bloc_client.function_run_log import FunctionRunMsg
from bloc_client.function_run_process_report import HighReadableFunctionRunProgress


class FunctionRunMsgQueue:
    def __init__(self) -> None:
        self._queue = Queue()

    @classmethod
    def New(cls):
        return cls()
    
    def report_log(self, log_level:LogLevel, msg: str):
        self._queue.put(
            FunctionRunMsg(level=log_level, msg=msg)
        )
    
    def report_high_readable_process(
        self,
        process_percent: Optional[float]=None,
        process_stage_index: Optional[int]=None,
        process_high_readable_msg: Optional[str]=None,
    ):
        if not any([
            process_percent, process_stage_index, process_high_readable_msg
        ]):
            return
        self._queue.put(
            HighReadableFunctionRunProgress(
                progress_percent=process_percent,
                msg=process_high_readable_msg,
                process_stage_index=process_stage_index
            )
        )
    
    def report_function_run_finished_opt(
        self, func_run_opt: FunctionRunOpt
    ):
        self._queue.put(
            func_run_opt
        )
    
    def get(self) -> Any:
        return self._queue.get(True)
