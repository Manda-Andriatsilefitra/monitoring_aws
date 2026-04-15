import json
import logging
from services.message_slack_service import put_message_slack

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Dictionnaire contenant les émojis
config_emoji = {
    "fatal": {"emoji": "🚨 FATAL"},
    "error": {"emoji": "❌ ERROR"},
    "warning": {"emoji": "⚠️ WARNING"},
    "info": {"emoji": "ℹ️ INFO"},
}


def lambda_handler(event, context):
    print(f"evenement : {event}")
    # Format message via SNS event["Records"]
    for record in event["Records"]:
        try:
            data = json.loads(record["Sns"]["Message"])
            app_name = data.get("applicationName")
            client = data.get("platform")
            env = data.get("env")

            # On formate le subject pour la lisibilité
            subject = (
                f"{client} {app_name} {env}"
            )

            # Les éléments pour le message
            canal = data.get("channel")
            logger.info(f"Le canal webhook: {canal}")
            
            request_id = data.get("requestId")
            message1 = data.get("slackMessage1")
            message2 = data.get("slackMessage2")

            # On récupère le niveau d'alert pour spécifier l'émoji
            type_alert = data.get("type")

            alert_emoji = config_emoji[type_alert].get("emoji")

            lines = [f"*{alert_emoji} {subject.upper()}*"]

            lines.append(f"{message1}. {message2}")

            lines.append(f"Id du requête: {request_id}")

            message_text = "\n".join(lines)

            put_message_slack(canal, message_text)
        except Exception as e:
            print(f"Erreur lors du traitement du message venant de sns: {str(e)}")
            raise e

        return {"message": "Envoie vers slack finit"}
