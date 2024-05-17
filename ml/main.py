import pika

from inference import toxicity_check
from load_env import RABBITMQ_DEFAULT_PASS
from load_env import RABBITMQ_DEFAULT_USER


if __name__ == "__main__":
    credentials = pika.credentials.PlainCredentials(
        username=RABBITMQ_DEFAULT_USER,
        password=RABBITMQ_DEFAULT_PASS,
    )
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host="rabbitmq",
            port=5672,
            credentials=credentials,
        )
    )

    channel_receiver = connection.channel()
    channel_sender = connection.channel()

    channel_sender.queue_declare(queue="result")
    channel_receiver.queue_declare(queue="check")

    def callback(ch, method, properties, body):
        message = body
        print("CALLBACK")
        result = toxicity_check(message)

        # send result of analysis to rabbit queue
        channel_sender.basic_publish(
            exchange="",
            routing_key="result",
            body=result
        )

    # get a tg message from rabbit queue
    channel_receiver.basic_consume(
        queue='check',
        on_message_callback=callback,
        auto_ack=True
    )
    channel_receiver.start_consuming()
