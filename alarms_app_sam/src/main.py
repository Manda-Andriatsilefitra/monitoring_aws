import logging
from abc import ABC, abstractmethod
from alarms_app_sam.src.service.alarms_service import main_threshold
from service.sns_service import put_sns_service

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):

    requestId = context.aws_request_id

    message = main_threshold(event, requestId)

    id_message = put_sns_service(message_body=message)

    logger.info(f"Le message d\'alarm avec l\'ID : \'{id_message}\' est envoyé vers SNS")

