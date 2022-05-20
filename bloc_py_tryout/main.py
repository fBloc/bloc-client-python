import asyncio

from bloc_client import BlocClient

from bloc_py_tryout.math_calcu import MathCalcu

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
