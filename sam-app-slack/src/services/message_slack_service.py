import os
import json
import boto3
import logging
import urllib3
from botocore.exceptions import ClientError

ssm = boto3.client("ssm")

logger = logging.getLogger()
logger.setLevel(logging.INFO)

webhook_token_param_name: str = str(os.getenv("SSM_PARAM_SLACK_TOKEN"))
webhook_url_param_name = os.getenv("SSM_PARAM_URL_WEBHOOK_APP") 

# Fonction pour récupérer string dans SSM parameter store
def get_ssm_parameter(name, decrypt=False):
    """Methode pour recupérer la valeur d un parameter ssm

    Args:
        name (string): Nom du parameter SSM
        decrypt (bool, optional): . Defaults to False.

    Returns:
        string: la valeur du parameter ssm
    """
    try:
        res = ssm.get_parameter(Name=name, WithDecryption=decrypt)
        return res["Parameter"]["Value"]
    except ClientError as e:
        # On récupère le code d'erreur
        error_code = e.response["Error"]["Code"]
        if error_code == "ParameterNotFound":
            logger.error(
                f"Erreur : Le paramètre '{name}' n'existe pas dans SSM."
            )
        elif error_code == "AccessDeniedException":
            logger.error("Erreur : Droits IAM insuffisants pour lire ce paramètre.")
        else:
            logger.error(
                f"Erreur AWS imprévue : {error_code} - {e.response['Error']['Message']}"
            )
    except Exception as e:
        logger.error("Erreur: Impossible de contacter le service parameter store.")
    return None

# Fonction pour récupérer le token de l'application slack depuis ssm
def get_slack_token():
    """fonction pour récupérer le token de l'application slack en utilisant la méthode _get_ssm_parameter()

    Returns:
        string: le token de l'application webhook
    """
    print(f"Récupération du token de l application webhook depuis ssm paramaeter store {webhook_token_param_name}")
    val = get_ssm_parameter(webhook_token_param_name, decrypt=True)
    if not val:
        return "token"
    return val

# Fonction pour récupérer l'url du webhook depuis ssm
def get_slack_webhook_url():
    """fonction pour récupérer l'url de l'application slack en utilisant la méthode _get_ssm_parameter()

    Returns:
        string: l'url de l'application webhook
    """
    print(f"Récupération de l url de l'application webhook depuis ssm paramaeter store {webhook_url_param_name}")
    val = get_ssm_parameter(webhook_url_param_name)
    if not val: return "url_webhook"
    return val

# FOnction d'nvoie de message vers slack
def put_message_slack(canal, corps_message):
    http = urllib3.PoolManager()

    webhook_token = get_slack_token()
    if not webhook_token:
            logger.error("Une erreur lors de la récupération du token webhook")

    webhook_url: str = get_slack_webhook_url()
    if not webhook_url:
        logger.error("Une erreur lors de la récupération de l'url webhook")

    headers = {
        "Authorization": f"Bearer {webhook_token}",
        "Content-Type": "application/json; charset=utf-8",
    }

    payload = {
        "channel": canal,  # Ex: "#general"
        "text": corps_message,
    }

    try:
        encoded_data = json.dumps(payload).encode("utf-8")
        response = http.request("POST", webhook_url, headers=headers, body=encoded_data)

        # Vérifier si la réponse est vide
        if not response.data:
            logger.error("L'API Slack a renvoyé une réponse vide.")
            return 
        try:
            res_data = json.loads(response.data.decode("utf-8"))

            if res_data.get("ok"):
                print(f"Message envoyé avec succès dans le canal {canal}")
            else:
                print(f"Erreur : {res_data.get('error')}")
        except json.JSONDecodeError:
            logger.error(f"Réponse Slack non-JSON reçue : {response.data}")

    except Exception as e:
        print(f"Erreur lors de l'appel HTTP : {str(e)}")