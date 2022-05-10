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
                        value_type=ValueType.intValueType,
                        formcontrol_type=FormControlType.FormControlTypeInput,
                        hint="input integer numbers",
                        default_value=None,
                        allow_multi=True,
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
                        formcontrol_type=FormControlType.FormControlTypeSelect,
                        hint="+/-/*/%",
                        allow_multi=False,
                        default_value=None,
                        select_options=[SelectOption(label=i.name, value=i.value) for i in ArithmeticOperators]
                    ),
                ]
            )
        ]
    
    def opt_config(self) -> List[FunctionOpt]:
        return [
            FunctionOpt(
                key="result",
                description="arithmetic operation result",
                value_type=ValueType.intValueType,
                is_array=False)
        ]
    
    def all_progress_milestones(self) -> List[str]:
        return [
            "start parsing ipt", 
            "start do the calculation", 
            "finished do the calculation"]
    
    def run(
        self, 
        ipts: List[FunctionIpt], 
        queue: FunctionRunMsgQueue
    ) -> FunctionRunOpt:
        # logger msg will be reported to bloc-server and can be represent in the frontend
	    # which means during this function's running, the frontend can get the realtime log msg
        # queue.report_log(LogLevel.info, "start")

        # AllProcessStages() index 0 - "start parsing ipt". which also will be represented in the frontend immediately.
        queue.report_high_readable_progress(progress_milestone_index=0)

        numbersSlice = ipts[0].components[0].value
        if not numbersSlice:
            queue.report_function_run_finished_opt(
                FunctionRunOpt(
                    suc=False, intercept_below_function_run=True,
                    error_msg="parse ipt `numbers` failed")
            )
            return

        try:
            operator = ArithmeticOperators(ipts[1].components[0].value)
        except ValueError:
            queue.report_function_run_finished_opt( 
                FunctionRunOpt(
                    suc=False, intercept_below_function_run=True,
                    error_msg=f"""arithmetic_operator({ipts[1].components[0].value}) not in {list(map(lambda c: c.value, ArithmeticOperators))}"""
                )
            )
            return
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
        elif operator == ArithmeticOperators.multiplication:
            ret = numbersSlice[0]
            for i in numbersSlice[1:]:
                ret //= i
        
        queue.report_high_readable_progress(progress_milestone_index=2)
        queue.report_function_run_finished_opt(
            FunctionRunOpt(
                suc=True, 
                optKey_map_data={
                    'result': ret
                }
            )
        )


if __name__ == "__main__":
    client = BlocClient.new_client("")
    opt = client.test_run_function(
        MathCalcu(),
        [
            [  # ipt 1 group, numbers
                [1, 2],
            ],
            [1]  # ipt 2 group, arithmetic operator
        ],
    )
    assert isinstance(opt, FunctionRunOpt), "opt should be FunctionRunOpt"
    assert opt.suc, "opt.suc should be True"
    assert "result" in opt.optKey_map_data, "opt.optKey_map_data should have key `result`"
    assert opt.optKey_map_data["result"] == 3, "opt.optKey_map_data['result'] should be 3"
