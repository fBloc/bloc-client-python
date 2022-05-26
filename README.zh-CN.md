# bloc-client-python
[bloc](https://github.com/fBloc/bloc)的python client SDK

可以基于此SDK使用开发基于python语言的 `bloc function`

在继续之前，请确保你已经大概了解了[bloc](https://github.com/fBloc/bloc)是什么，并且已经通过[教程](https://github.com/fBloc/bloc/blob/main/docs/guide/deploy_local_environment_guide.md)在本地环境部署了bloc环境

## bloc function是什么？
bloc function就是开发者通过对应语言的bloc client SDK开发的一个函数，其在部署后便能够被用户在bloc前端看到，并可被编入工作流进行组合和自定义设置参数。待到对应工作流执行时到此函数时，就会按照用户在前端配置的参数进行执行并上报运行信息和运行结果到bloc。

## 开发bloc function教程
这里我们通过编写一个简单的 bloc function来进行说明。

其接收多个整数，并且接收一个特定的算法。然后对那些数字执行对应的算法

### 准备
- 创建目录
    ```shell
    mkdir bloc_py_tryout && cd bloc_py_tryout
    ```
- 如果需要的话，请按照你习惯的方式创建一个虚拟环境
- 安装python版本的bloc client SDK:
    ```shell
    pip install bloc_client
    ```

### 编写bloc function
1. 首先创建一个对象、其表示了这个bloc function节点
    ```python
    # math_calcu.py
    class MathCalcu(FunctionInterface):
    ```
    而后此bloc function 需要实现 [FunctionInterface](https://github.com/fBloc/bloc-client-python/blob/main/bloc_client/function_interface.py#L10).

2. 实现 ipt_config() 方法 - 其描述了此function需要的入参:
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

3. 实现 opt_config() - 其描述了此function需要的出参:
    ```python
    def opt_config(self) -> List[FunctionOpt]:
        # 这里也返回成list数据类型，是为了在前端能够显示为一个固定的顺序
        return [
            FunctionOpt(
                key="result",
                description="arithmetic operation result",
                value_type=ValueType.intValueType,
                is_array=False)
        ]
    ```

4.  实现 all_progress_milestones() - 其定义了此函数在运行进度过程中的高可读的里程碑事件

    此设计主要是为运行时间较长的函数准备的。当其正在运行时，其可以上报自己当前运行到的进度里程碑。从而关心进度的人能够在bloc前端看到此信息。如果你的bloc function很快就能运行完成，那就没必要设置这个了。

    ```python
    def all_progress_milestones(self) -> List[str]:
        return [
            "parsing ipt", 
            "in calculation", 
            "finished"]
    ```


5. 实现 run() - 真正的执行逻辑:
    ```python
    def run(
        self, 
        ipts: List[FunctionIpt], 
        queue: FunctionRunMsgQueue
    ) -> FunctionRunOpt:
        # 日志信息会被立即上传到bloc并能在bloc前端被访问到
        # 也就是说运行中的函数，其实时日志能在bloc前端看到
        queue.report_log(LogLevel.info, "start")

        # 汇报进度里程碑：这里的汇报索引是0。其也能实时在bloc前端被看到
        queue.report_high_readable_progress(progress_milestone_index=0)

        numbersSlice = ipts[0].components[0].value
        if not numbersSlice:
            queue.report_function_run_finished_opt(
                FunctionRunOpt(
                    suc=False,  # 函数运行失败了
                    intercept_below_function_run=True,  # 拦截此节点下游节点的运行
                    error_msg="parse ipt `numbers` failed",  # 报错描述
                )
            )
            # 当函数运行失败时，也可以选择不拦截其下游的运行
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
- 到此，我们完成了bloc function的核心定义代码。接下来我们它写测试代码

### 编写单元测试代码
- 在`math_calcu_test.py`中编写简单的测试:
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
- 运行 `python math_calcu_test.py`, 你会看到`OK`, 表示你开发的函数的运行满足你的预期
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

### 向 bloc-server 汇报
当通过编写足够的测试确认你的函数运行没有问题了之后，你可以通过部署它来向bloc-server进行汇报

这里我假设你已经通过[教程](https://github.com/fBloc/bloc/blob/main/docs/guide/deploy_local_environment_guide.md)部署了一套本地bloc环境。如果是的话、请继续。

- 在 `bloc_py_tryout` 目录创建一个`main.py`文件，并写入内容:
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
- 运行:
    ```shell
    $ python run main.py
    ```

- 运行成功后，此bloc function就成功提交到bloc了。从而你可以在bloc web端看到与使用此function了（如果你刚刚接触bloc web端、不清楚有哪些操作，可见[教程](https://docs.blocapp.xyz/docs/category/web%E7%AB%AF%E5%8A%9F%E8%83%BD%E7%AE%80%E4%BB%8B)）

### 完整代码
[这里](https://github.com/fBloc/bloc-client-python/tree/main/bloc_py_tryout)

## 其他资料
- 你可以在[这里](https://github.com/fBloc/bloc-function-demo-py) 找到更多更复杂的bloc function例子