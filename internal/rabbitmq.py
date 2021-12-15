import asyncio
from typing import Callable

import pika

ExchangeName = "bloc_topic_exchange"


class RabbitMQ:
    def __init__(
            self,
            user: str, password: str,
            host: str, port: int, v_host: str
    ) -> None:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=host, port=port,
                virtual_host=v_host,
                credentials=pika.PlainCredentials(user, password)
            ))

        channel = connection.channel()
        channel.basic_qos(prefetch_count=1)
        channel.exchange_declare(exchange=ExchangeName, exchange_type='topic')

        self._channel = channel
    
    async def consume_rabbit_exchange(
        self,
        queue_name: str,
        routing_key: str,
        callback_func: Callable,
    ):
        self._channel.exchange_declare(exchange=ExchangeName, exchange_type='topic', durable=True)
        self._channel.queue_declare(queue_name, durable=True, exclusive=False, auto_delete=False)
        self._channel.queue_bind(exchange=ExchangeName, queue=queue_name, routing_key=routing_key)

        while True:
            for method_frame, properties, body in self._channel.consume(
                queue=queue_name,
                inactivity_timeout=1.1,
                auto_ack=True,
                exclusive=False,
            ):
                if not body:
                    await asyncio.sleep()
                    continue
                await callback_func(body.decode(), method_frame.delivery_tag)
