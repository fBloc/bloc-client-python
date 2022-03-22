# bloc-client-python
The python language client SDK for [bloc](https://github.com/fBloc/bloc).

You can develop bloc's function node in python language based on this SDK.

First make sure you already have a knowledge of [bloc](https://github.com/fBloc/bloc) and already have deployed a bloc-server instance.

## How to use
Let's write a simple function which receive some integers and do a designated mathematical calculation to these integers.

### prepare
create a python program directory and initial it:
```shell
$ mkdir bloc_python_tryout
$ cd bloc_python_tryout
```

install sdk:
```shell
$ pip install bloc_client
```

create a folder to hold function:
```shell
$ mkdir function
```

### write the function
1. first create a class which stand for the function node:
`math_calcu.py`
```python
class MathCalcu(FunctionInterface):
```

then the function node should implement the [interface](https://github.com/fBloc/bloc-client-python/blob/c7b3c6dfadef950dbdbc141c8cc1351a6495e615/bloc_client/function_interface.py#L10).

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
```

3. implement opt_config() which defined function node's opt:
```python
def opt_config(self) -> List[FunctionOpt]:
    return [
        FunctionOpt(
            key="result",
            description="arithmetic operation result",
            value_type=ValueType.intValueType,
            is_array=False)
    ]
```

4. implement all_process_stages() which define the highly readable describe stages of the function node's run:

This is designed 4 long run function, during it is running, it can report it's current running stage for the user in frontend to get the information.

If your function is quick run. maybe no need to set it and just return blank.

```python
def all_process_stages(self) -> List[str]:
    return [
        "start parsing ipt", 
        "start do the calculation", 
        "finished do the calculation"]
```


5. implement run() which do the real work:
```python
// Run do the real work
def run(
    self, 
    ipts: List[FunctionIpt], 
    queue: FunctionRunMsgQueue
) -> FunctionRunOpt:
    # logger msg will be reported to bloc-server and can be represent in the frontend
    # which means during this function's running, the frontend can get the realtime log msg
    # queue.report_log(LogLevel.info, "start")

    # AllProcessStages() index 0 - "start parsing ipt". which also will be represented in the frontend immediately.
    queue.report_high_readable_process(process_stage_index=0)

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
    queue.report_high_readable_process(process_stage_index=1)

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
    
    queue.report_high_readable_process(process_stage_index=2)
    queue.report_function_run_finished_opt(
        FunctionRunOpt(
            suc=True, 
            optKey_map_data={
                'result': ret
            }
        )
    )
```

ok, we finished write the function

### write test of the function
write a simple example to test the function:
```python
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
```

Run `python function/math_calcu.py`, if not raised exception, the test passed.
Which means your function run meet your expectation.

### report to the server
after make sure your function runs well, you can deploy it.

During `bloc_python_tryout` directory and make a `main.py` file with content:
```python
import asyncio

from bloc_client import BlocClient

from function import math_calcu

async def main():
    client_name = "tryout-python"
    bloc_client = BlocClient(name=client_name)

    fake_rabbit_port = 6696
    fake_bloc_server_port = 80
    bloc_client.get_config_builder(
    ).set_server(
		"$bloc_server", fake_bloc_server_port,
    ).set_rabbitMQ(
        user="$user", password='$password',
        host="$host", port=fake_rabbit_port
    ).build_up()

    pyClient_func_group = bloc_client.register_function_group("math")
    pyClient_func_group.add_function(
        "calcu", # name your function node's name
		"receive numbers and do certain math operation to them", # the describe of your function node
		math_calcu(), # your function implement
    )

    await bloc_client.run()


if __name__ == "__main__":
    asyncio.run(main())
```

after replace the configs, input your bloc-server's address and rabbit address.

you can run it by:
```shell
$ python run main.py
```

after suc run, this client's all function node are registered to the bloc-server, which can be see and operate in the frontend, and this client will receive bloc-server's trigger function to run msg and run it.

demo code is [here](/examples/bloc_py_tryout/).