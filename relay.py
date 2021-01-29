import asyncio
from bergen.clients.default import Bergen
import aiormq
import aiormq.types
import json

client = Bergen(
        host="p-tnagerl-lab1",
        port=8000,
        client_id="y1W8JK5OgpAexf68eqbHIx60228rTBc4moNlaKYN", 
        client_secret="ovChuVgIFFQcNT3buPbm5AVjGCJGHBQZOQTqhvzwP02IllfJRVj17efit6aGqPcd01AJPY1SCc8kTBM22pistp8A1BRQRmtgX9Nycd2LcN1YEduhjpSY9mq5Pm2nV0xi",
        name="karl",# if we want to specifically only use pods on this innstance we would use that it in the selector
)

def fib(n):
    if n == 0:
        return 0
    elif n == 1:
        return 1
    else:
        return fib(n-1) + fib(n-2)


async def on_message(message:aiormq.types.DeliveredMessage):

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


    await message.channel.basic_publish(
        "hahah".encode(), routing_key=message.header.properties.reply_to,
        properties=aiormq.spec.Basic.Properties(
            correlation_id=message.header.properties.correlation_id
        ),

    )

    await message.channel.basic_ack(message.delivery.delivery_tag)
    print('Request complete')


async def main():
    # Perform connection
    connection = await aiormq.connect(f"amqp://{client.token}:guest@localhost/")

    # Creating a channel
    channel = await connection.channel()

    # Declaring queue
    declare_ok = await channel.queue_declare('my_queue')

    # Start listening the queue with name 'hello'
    await channel.basic_consume(declare_ok.queue, on_message)


loop = asyncio.get_event_loop()
loop.create_task(main())

# we enter a never-ending loop that waits for data
# and runs callbacks whenever necessary.
print(" [x] Awaiting RPC requests")
loop.run_forever()