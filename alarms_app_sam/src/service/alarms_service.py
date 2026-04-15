import logging
import json
from service.parser_service import StandardPathParser, QueuePathParser

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def main_threshold(event, requestId):
    try:
        # --- Extraction sécurisée des infos de l'alarme ---
        detail = event.get("detail", {})
        alarm_name = detail.get("alarmName", "Inconnu")
        state = detail.get("state", {})
        previous_state = detail.get("previousState", {})

        queue_name = "Inconnu"

        log_group_name = "Inconnu"

        # Initier les variables pour l'environnement des ressources
        client, app_name, environnement = (
            "client-inconnu",
            "application-inconnu",
            "environnement-inconnu",
        )

        metrics = detail.get("configuration", {}).get("metrics", [])
        if metrics and len(metrics) > 0:
            metric_stat = metrics[0].get("metricStat", {})
            metric = metric_stat.get("metric", {})
            namespace = metric.get("namespace", "N/A")
            period_seconds = metric_stat.get("period")
            dimensions = metric.get("dimensions", {})

            # Récupération du nom de la queue
            if "QueueName" in dimensions:
                queue_name = dimensions["QueueName"]
            elif "Queue" in dimensions:
                queue_name = dimensions["Queue"]
            elif "LogGroupName" in dimensions:
                log_group_name = dimensions.get("LogGroupName")

            reason_data_str = state.get("reasonData") or previous_state.get(
                "reasonData"
            )

            threshold = None
            threshold_display = "Inconnu"

            # Formater le message pour le type de ressource "AWS/Logs"
            if namespace == "AWS/Logs":
                # Alarm absence de logs
                if period_seconds:
                    period_minutes = period_seconds // 60
                    period_text = f"{period_minutes} derinère(s) minute(s)"
                else:
                    period_text = "des dernières minutes configurées"

                parser_standard = StandardPathParser()
                client, app_name, environnement = parser_standard.parse(log_group_name)

                slack_message1: str = f"Log Group: {log_group_name}"
                slack_message2: str = f"Aucun log reçu au cours des {period_text}"

            # Formater le message pour les types de ressources "AWS/SQS" et "AWS/AmazonMQ"
            elif namespace in ["AWS/SQS", "AWS/AmazonMQ"]:
                if reason_data_str:
                    reason_data = json.loads(reason_data_str)
                    threshold = reason_data.get("threshold")

                    if (
                        threshold is not None
                        and isinstance(threshold, (int, float))
                        and float(threshold).is_integer()
                    ):
                        threshold_display = int(threshold)
                    else:
                        if threshold is not None:
                            threshold_display = threshold

                parser_queue = QueuePathParser()
                client, app_name, environnement = parser_queue.parse(queue_name)

                slack_message1: str = f"Queue: {queue_name}"
                slack_message2: str = (
                    f"La file d'attente dépasse le seuil {threshold_display}"
                )

            else:
                # Au cas où l'alarm provient d'autres ressources inconnus
                slack_message1: str = f"Alarme CloudWatch: {alarm_name}"
                slack_message2: str = (
                    f"Type de ressource non reconnu (Namespace: {namespace})"
                )

            # Le type d'alert (niveau)
            type_alert = "error"

            # Le nom du canal webhook (à définir selon les besoins)
            channel_slack = app_name

            message_body = {
                "type": type_alert,
                "platform": client,
                "applicationName": app_name,
                "env": environnement,
                "slackMessage1": slack_message1,
                "slackMessage2": slack_message2,
                "requestId": requestId,
                "slack": True,
                "channel": channel_slack,
            }
            return message_body

    except Exception as e:
        logger.error(f"Erreur lors de la formatage de message pour sns")
