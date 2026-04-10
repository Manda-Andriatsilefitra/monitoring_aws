import os
import json
import boto3
import logging
import base64
import gzip
from abc import ABC, abstractmethod

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Une fonction qui récupère des événement de log suscription avec un pattern error et envoie le message vers SNS

# Abstraction du Parsing
class LogGroupParser(ABC):
    """Interface pour définir comment extraire les infos du nom du Log Group."""

    @abstractmethod
    def parse(self, log_name: str):
        """
        Extrait les métadonnées à partir du nom d'un groupe de logs.

        Args:
            log_name (str): Le nom complet du Log Group CloudWatch.

        Returns:
            tuple: Un tuple contenant les informations extraites (ex: service, environnement).

        Raises:
            NotImplementedError: Si la sous-classe ne définit pas cette méthode.
        """
        pass  # aucune implémentation par défaut.


class StandardPathParser(LogGroupParser):
    """Format: /entreprise/plateforme/app_name"""

    def parse(self, log_name: str):
        """Methode pour parser le nom du log group pour obtenir le nom de l'application et la plateforme pour usage dans les alerts

        Args:
            log_name (str): nom du log group

        Returns:
            str, str: nom de l'application et la plateforme
        """
        parts = log_name.strip("/").split("/")
        if len(parts) >= 3:
            client = parts[0]
            environnement = parts[1]
            app_name = parts[2]
            return client, app_name, environnement
        return "client-inconnue", "app-inconnue", "plateforme-inconnue"



def lambda_handler(event, context):

    sns_client = boto3.client("sns")
    SNS_TOPIC_ARN = os.environ["SNS_TOPIC_ARN"]

    # print(f"Événement reçu : {event}")

    # Décoder base64
    compressed_payload = base64.b64decode(event['awslogs']['data'])
    # Décompresser GZIP
    uncompressed_payload = gzip.decompress(compressed_payload)
    # Parser le JSON
    log_data = json.loads(uncompressed_payload)

    log_group_name = log_data['logGroup']

    requestId = context.aws_request_id

    message_content = log_data['logEvents'][0]['message']

    parser_standard = StandardPathParser()
    client, app_name, environnement = parser_standard.parse(log_group_name)

    # Le type d'alert (niveau)
    type_alert="error"

    # Le nom du canal webhook
    channel_slack=app_name

    # Construction du message à envoyer vers sns
    message_body = {
        "type": type_alert,
        "platform": client,
        "applicationName": app_name,
        "env": environnement,
        "requestId": requestId,
        "slackMessage1": f"ERROR LOG GROUP: {log_group_name}",
        "slackMessage2": message_content,
        "slack": True,
        "channel": channel_slack
    }

    # --- Construction du message ---
    subject = f"[{client.upper()}] - [{app_name.upper()}] - [{environnement.upper()}]"

    try:
        sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=subject,
            Message=json.dumps(message_body),
        )
        return {"status": "sent"}
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi SNS: {e}")
        return {"status": "error", "message": str(e)}
