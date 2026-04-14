import json
import logging
import base64
import gzip
from parser_service import StandardPathParser

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def format_handler(event, requestId):

    # print(f"Événement reçu : {event}")

    try:
        # Décoder base64
        compressed_payload = base64.b64decode(event['awslogs']['data'])
        if not compressed_payload:
            logger.error("Erreur lors de la récupération des données de la subscription filter")

        # Décompresser GZIP
        uncompressed_payload = gzip.decompress(compressed_payload)
        if not uncompressed_payload:
            logger.error("Impossible de décomprésser le donnée depuis l'alert subscription filter")

        # Parser le JSON
        log_data = json.loads(uncompressed_payload)

        log_group_name = log_data['logGroup']

        # requestId = context.aws_request_id

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

        return message_body
    
    except Exception as e:
        logger.error(f"Erreur lors de la formatage de message pour l\'alerte subscription filter")
