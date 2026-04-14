import os
import json
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def put_sns_service(message_body):

    sns_client = boto3.client("sns")
    SNS_TOPIC_ARN = os.environ["SNS_TOPIC_ARN"]

    target = "slack"
    try:
        response = sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=json.dumps(message_body),
            MessageAttributes={"destinataire": {"DataType": "String", "StringValue": target}},
        )
        return response["MessageId"]

    except Exception as e:
        logger.error(f"Erreur lors de l'envoie du message vers sns: {e}")