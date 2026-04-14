import logging
from abc import ABC, abstractmethod

logger = logging.getLogger()
logger.setLevel(logging.INFO)


# Abstraction du Parsing
class Parser(ABC):
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


class StandardPathParser(Parser):
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

class QueuePathParser(Parser):
    """Format: /entreprise/plateforme/app_name"""

    def parse(self, log_name: str):
        """Methode pour parser le nom du log group pour obtenir le nom de l'application et la plateforme pour usage dans les alerts

        Args:
            log_name (str): nom du log group

        Returns:
            str, str: nom de l'application et la plateforme
        """
        parts = log_name.strip("-").split("-")
        if len(parts) >= 3:
            client = parts[0]
            environnement = parts[1]
            app_name = parts[2:]
            return client, app_name, environnement
        return "client-inconnue", "app-inconnue", "plateforme-inconnue"