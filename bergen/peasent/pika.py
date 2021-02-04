import asyncio
from bergen.messages.assignation import AssignationMessage
from bergen.schema import Template
from bergen.peasent.base import BasePeasent
import json
import aiormq
from aiostream import stream
    


class PikaPeasent(BasePeasent):
    """ BROKEN AS FOR NOW """

    async def on_message(self, message:aiormq.types.DeliveredMessage):

        assignation = AssignationMessage.from_message(message=message)

        message_body = json.loads(message.body.decode())

        assert "meta" in message_body, "No meta provided, check Arnheim Schema"
        assert "data" in message_body, "No meta provided, check Arnheim Schema"


        if "progress" in message_body["meta"]:
            print("Updating Progress")
            await message.channel.basic_publish(
            "Started".encode(), routing_key=message_body["meta"]["progress"],
            properties=aiormq.spec.Basic.Properties(
                correlation_id=message.header.properties.correlation_id
            ),

        )

        #xs = stream.count(interval=10)

        #async with xs.stream() as streamer:

          #async for t in streamer:
        
        def worker(inputs):
            return {"rep": 1}

        result = worker(assignation.data.inputs)

        assignation.data.outputs = result

        await message.channel.basic_publish(
            assignation.to_message(), routing_key=message.header.properties.reply_to,
            properties=aiormq.spec.Basic.Properties(
                correlation_id=message.header.properties.correlation_id
            ),

        )
        print(f"Yielding {assignation.data.id}")

        await message.channel.basic_ack(message.delivery.delivery_tag)
        print('Request complete')


    async def configure(self):
        # Perform connection
        connection = await aiormq.connect(f"amqp://{self.token}:guest@localhost/")
        channel = await connection.channel()

        # Declaring queue
        pod_assignment_queue = await channel.queue_declare('pod_two')

        # Start listening the queue with name 'hello'
        await channel.basic_consume(pod_assignment_queue.queue, self.on_message)

        return pod_assignment_queue.queue









    