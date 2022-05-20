# bloc-client-python
The python language client SDK for [bloc](https://github.com/fBloc/bloc).

You can develop bloc's function node in python language based on this SDK.

First make sure you already have a knowledge of [bloc](https://github.com/fBloc/bloc) and already have deployed a local test bloc environment(see [deploy a local bloc environment](https://github.com/fBloc/bloc/blob/main/docs/guide/deploy_local_environment_guide.md)).

## Develop bloc function node tutorial
Let's write a simple bloc function node which receive some integers and do a designated mathematical calculation to these integers.

### prepare
- create a python program directory and initial it:
    ```shell
    mkdir bloc_py_tryout && cd bloc_py_tryout
    ```
- create virtual environment by yourself
- install sdk:
    ```shell
    pip install bloc_client
    ```

### write bloc function node
1. first create a class which stand for the function node:
    ```python
    # math_calcu.py
    class MathCalcu(FunctionInterface):
    ```
    then the function node should implement the [FunctionInterface](https://github.com/fBloc/bloc-client-python/blob/main/bloc_client/function_interface.py#L10).

2. implement ipt_config() which defined function node's input params:
    ```python
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
    ```

3. implement opt_config() which defined function node's opt:
    ```python
    def opt_config(self) -> List[FunctionOpt]:
        # returned list type for a fixed order to show in the frontend which lead to a better user experience
        return [
            FunctionOpt(
                key="result",
                description="arithmetic operation result",
                value_type=ValueType.intValueType,
                is_array=False)
        ]
    ```

4. implement all_progress_milestones() which define the highly readable describe milestones of the function node's run:

    all_progress_milestones() is designed for long run function, during it is running, it can report it's current running milestone for the user in frontend to get the information.If your function is quick run. maybe no need to set it and just return blank.

    ```python
    def all_progress_milestones(self) -> List[str]:
        return [
            "parsing ipt", 
            "in calculation", 
            "finished"]
    ```


5. implement run() which do the real work:
    ```python
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
        elif operator == ArithmeticOperators.multiplication:
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
    ```
- By now, we finished write the code of a bloc function node, next we will write unit test code to this function node

### write unit test
- write a simple unit test in `math_calcu_test.py`:
    ```python
    # math_calcu_test.py
    import unittest

    from bloc_client import *

    from math_calcu import MathCalcu

    class TestMathCalcuNode(unittest.TestCase):
        def setUp(self):
            self.client = BlocClient.new_client("")

        def test_add(self):
            opt = self.client.test_run_function(
                MathCalcu(),
                [
                    [  # ipt 0
                        [1, 2]  # component 0, numbers
                    ],
                    [  # ipt 1
                        1  # "+" operater
                    ],
                ]
            )
            assert isinstance(opt, FunctionRunOpt), "opt should be FunctionRunOpt type"
            self.assertIsInstance(opt, FunctionRunOpt, "opt is not FunctionRunOpt type")
            self.assertTrue(opt.suc, "should 	suc")
            self.assertFalse(opt.intercept_below_function_run, "should not intercept below function run")
            self.assertEqual(opt.optKey_map_data['result'], 3, "result should be 3")


    if __name__ == '__main__':
        unittest.main()
    ```
- Run `python math_calcu_test.py`, you will see the OK. which means your function run meet your expectation.
    ```python
    $ python math_calcu_test.py
    2022-05-20 17:46:39,989 INFO received log msg: FunctionRunMsg(level=<LogLevel.info: 'info'>, msg='start')
    2022-05-20 17:46:39,989 INFO progress msg: HighReadableFunctionRunProgress(progress_percent=None, msg=None, progress_milestone_index=0)
    2022-05-20 17:46:39,989 INFO progress msg: HighReadableFunctionRunProgress(progress_percent=None, msg=None, progress_milestone_index=1)
    2022-05-20 17:46:39,989 INFO progress msg: HighReadableFunctionRunProgress(progress_percent=None, msg=None, progress_milestone_index=2)
    2022-05-20 17:46:39,989 INFO run finished. opt is: FunctionRunOpt(suc=True, canceled=False, timeout_canceled=False, intercept_below_function_run=False, error_msg='', description='received 2 number', optKey_map_data={'result': 3}, optKey_map_objectStorageKey=None, optKey_map_briefData=None)
    .
    ----------------------------------------------------------------------
    Ran 1 test in 0.308s

    OK
    ```

### report to the server
After make sure your function runs well, you can deploy it to report to bloc.

I suppose you have already deployed a local bloc environment. if not, follow [guide](https://github.com/fBloc/bloc/blob/main/docs/guide/deploy_local_environment_guide.md) to deploy it.

- During `bloc_py_tryout` directory and make a `main.py` file with content:
    ```python
    import asyncio

    from bloc_client import BlocClient

    from math_calcu import MathCalcu

    async def main():
        client_name = "tryout-python"
        bloc_client = BlocClient(name=client_name)

        bloc_client.get_config_builder(
        ).set_server(
            "127.0.0.1", 8080,
        ).set_rabbitMQ(
            user="blocRabbit", password='blocRabbitPasswd',
            host="127.0.0.1", port=5672
        ).build_up()

        # create a function group
        pyClient_func_group = bloc_client.register_function_group("math")
        # register the function node to upper function group
        pyClient_func_group.add_function(
            "calcu", # name your function node's name
            "receive numbers and do certain math operation to them", # the describe of your function node
            MathCalcu(), # your function implement
        )

        await bloc_client.run()


    if __name__ == "__main__":
        asyncio.run(main())
    ```
- now run it:
    ```shell
    $ python run main.py
    ```

- After suc run, this client's all function node are registered to the bloc-server, which can be see and operate in the frontend, and this client will receive bloc-server's trigger function to run msg and do the execute. If you are first to the bloc web, you may check this [brief introduction to bloc web](#todo)

### total code 
you can find the demo code [here](https://github.com/fBloc/bloc-client-python/tree/main/bloc_py_tryout)

## Other references
- you can find more bloc function node examples [here](https://github.com/fBloc/bloc-function-demo-py)
