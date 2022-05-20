from typing import List
from enum import IntEnum

from bloc_client import *


class ArithmeticOperators(IntEnum):
    addition = 1
    subtraction = 2
    multiplication = 3
    division = 4


class MathCalcu(FunctionInterface):
    def ipt_config(self) -> List[FunctionIpt]:
        return [
            FunctionIpt(
                key="numbers",
                display="int numbers",
                must=True,
                components=[
                    IptComponent(
                        value_type=ValueType.intValueType,  # input value should be int type
                        formcontrol_type=FormControlType.FormControlTypeInput,  # frontend should use input
                        hint="input integer numbers",  # hint for user
                        allow_multi=True,  # multiple input is allowed
                    )
                ]
            ),
            FunctionIpt(
                key="arithmetic_operator",
                display="choose arithmetic operators",
                must=True,
                components=[
                    IptComponent(
                        value_type=ValueType.intValueType,
                        hint="+/-/*/%",
                        formcontrol_type=FormControlType.FormControlTypeSelect,  # frontend should use select
                        select_options=[  # select options
                            SelectOption(label=i.name, value=i.value) for i in ArithmeticOperators
                        ],
                        allow_multi=False,  # only allow single select value
                    ),
                ]
            )
        ]
    
    def opt_config(self) -> List[FunctionOpt]:
        # returned list type for a fixed order to show in the frontend which lead to a better user experience
        return [
            FunctionOpt(
                key="result",
                description="arithmetic operation result",
                value_type=ValueType.intValueType,
                is_array=False)
        ]
    
    def all_progress_milestones(self) -> List[str]:
        return [
            "parsing ipt", 
            "in calculation", 
            "finished"]
    
    def run(
        self, 
        ipts: List[FunctionIpt], 
        queue: FunctionRunMsgQueue
    ) -> FunctionRunOpt:
        # logger msg will be reported to bloc-server and can be represent in the frontend
	    # which means during this function's running, the frontend can get the realtime log msg
        queue.report_log(LogLevel.info, "start")

        # AllProcessStages() index 0 - "parsing ipt". which will be represented in the frontend immediately.
        queue.report_high_readable_progress(progress_milestone_index=0)

        numbersSlice = ipts[0].components[0].value
        if not numbersSlice:
            queue.report_function_run_finished_opt(
                FunctionRunOpt(
                    suc=False,  # function run failed
                    intercept_below_function_run=True,  # intercept flow's below function run (you can think like raise exception in the flow)
                    error_msg="parse ipt `numbers` failed",  # error description
                )
            )
            # suc can be false and intercept_below_function_run can also be false
			# which means this function node's fail should not intercept it's below function node's running
            return

        try:
            operator = ArithmeticOperators(ipts[1].components[0].value)
        except ValueError:
            queue.report_function_run_finished_opt( 
                FunctionRunOpt(
                    suc=False, 
                    intercept_below_function_run=True,
                    error_msg=f"""arithmetic_operator({ipts[1].components[0].value}) not in {list(map(lambda c: c.value, ArithmeticOperators))}"""
                )
            )
            return
        # AllProcessStages() index 1 - "in calculation". which also will be represented in the frontend immediately.
        queue.report_high_readable_progress(progress_milestone_index=1)

        ret = 0
        if operator == ArithmeticOperators.addition:
            ret = sum(numbersSlice)
        elif operator == ArithmeticOperators.subtraction:
            ret = numbersSlice[0] - sum(numbersSlice[1:])
        elif operator == ArithmeticOperators.multiplication:
            ret = numbersSlice[0]
            for i in numbersSlice[1:]:
                ret *= i
        elif operator == ArithmeticOperators.division:
            ret = numbersSlice[0]
            for i in numbersSlice[1:]:
                ret //= i
        
        queue.report_high_readable_progress(progress_milestone_index=2)
        queue.report_function_run_finished_opt(
            FunctionRunOpt(
                suc=True, 
                intercept_below_function_run=False,
                description=f"received {len(numbersSlice)} number",
                optKey_map_data={
                    'result': ret
                }
            )
        )
