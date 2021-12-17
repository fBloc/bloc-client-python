from os import path
from datetime import datetime
from typing import Optional, List, Tuple
from dataclasses import dataclass, field

from function_opt import FunctionOpt
from function_run_opt import FunctionRunOpt
from internal.http_util import get_to_server, post_to_server

FunctionRunRecordPath = "get_function_run_record_by_id"
FunctionRunFinishedPath = "function_run_finished"


@dataclass
class BriefAndKey:
    brief: str
    object_storage_key: str


@dataclass
class FunctionRunRecord:
    id: str
    flow_id: str
    function_id: str
    flow_run_record_id: str
    canceled: str
    ipt: List[List[BriefAndKey]] = field(default_factory=list)
    should_be_canceled_at: Optional[datetime]=None

async def get_functionRunRecord_by_id(
    server_url: str,
    func_run_record_id: str
) -> Tuple[FunctionRunRecord, Exception]:
    resp, err = await get_to_server(
        server_url + path.join(FunctionRunRecordPath, func_run_record_id),
        {})
    if err:
        return None, err

    try:
        ipts = []
        function_run_record = FunctionRunRecord(
            id=resp['id'],
            flow_id=resp['flow_id'],
            function_id=resp['function_id'],
            flow_run_record_id=resp['flow_function_id'],
            canceled=resp.get('canceled', False),
            ipt=ipts
        )
        # TODO 处理should_be_canceled_at字段
        for ipt in resp['ipt']:
            tmp = []
            for component in ipt:
                tmp.append(
                    BriefAndKey(
                        brief=component['brief'],
                        object_storage_key=component['object_storage_key']
                    )
                )
            ipts.append(tmp)

        return function_run_record, None
    except Exception as e:
        return None, e


async def report_function_run_finished(
    server_url: str,
    function_run_record_id: str, 
    function_run_opt: FunctionRunOpt,
) -> Exception:
    data = function_run_opt.finished_report_dict
    data['function_run_record_id'] = function_run_record_id
    resp, err = await post_to_server(
        server_url + path.join(FunctionRunFinishedPath),
        data)
    return err
