from typing import Dict, List, Any, Optional
import logging
from pathlib import Path
from .documentation_manager import DocumentationManager
from .config_manager import ConfigManager, ConfigurationError

logger = logging.getLogger(__name__)

class AgentInterface:
    def __init__(
        self,
        docs_manager: DocumentationManager,
        config_manager: ConfigManager
    ):
        self.docs_manager = docs_manager
        self.config_manager = config_manager

    async def read_documentation(self, doc_type: str) -> Dict[str, Any]:
        """
        Legge e analizza la documentazione.
        """
        try:
            content = self.docs_manager.read_documentation(doc_type)
            parsed = self.docs_manager.parse_markdown(content)
            logger.info(f"Documentazione {doc_type} letta con successo")
            return parsed

        except Exception as e:
            logger.error(f"Errore nella lettura della documentazione {doc_type}: {str(e)}")
            raise

    async def update_documentation(self, doc_type: str, content: str) -> None:
        """
        Aggiorna la documentazione esistente.
        """
        try:
            # Valida il contenuto Markdown
            parsed = self.docs_manager.parse_markdown(content)
            
            # Aggiorna il documento
            self.docs_manager.update_documentation(doc_type, content)
            logger.info(f"Documentazione {doc_type} aggiornata con successo")

        except Exception as e:
            logger.error(f"Errore nell'aggiornamento della documentazione {doc_type}: {str(e)}")
            raise

    async def get_configuration(self, config_name: str) -> Dict[str, Any]:
        """
        Recupera una configurazione.
        """
        try:
            config = self.config_manager.load_config(config_name)
            logger.info(f"Configurazione {config_name} recuperata con successo")
            return config

        except ConfigurationError as e:
            logger.error(f"Errore nel recupero della configurazione {config_name}: {str(e)}")
            raise

    async def validate_configuration(
        self,
        config_name: str,
        config_data: Dict[str, Any]
    ) -> bool:
        """
        Valida una configurazione contro il suo schema.
        """
        try:
            schema = self.config_manager.get_config_schema(config_name)
            self.config_manager.validate_config(config_data, schema)
            logger.info(f"Configurazione {config_name} validata con successo")
            return True

        except ConfigurationError as e:
            logger.error(f"Errore nella validazione della configurazione {config_name}: {str(e)}")
            return False

    async def update_configuration(
        self,
        config_name: str,
        config_data: Dict[str, Any]
    ) -> None:
        """
        Aggiorna una configurazione dopo validazione.
        """
        try:
            # Valida la configurazione
            if not await self.validate_configuration(config_name, config_data):
                raise ConfigurationError(f"Configurazione {config_name} non valida")
            
            # Salva la configurazione
            self.config_manager.save_config(config_name, config_data)
            logger.info(f"Configurazione {config_name} aggiornata con successo")

        except Exception as e:
            logger.error(f"Errore nell'aggiornamento della configurazione {config_name}: {str(e)}")
            raise

    async def get_documentation_version(
        self,
        doc_type: str,
        version: Optional[str] = None
    ) -> str:
        """
        Recupera una versione specifica della documentazione.
        """
        try:
            content = self.docs_manager.get_documentation_version(doc_type, version)
            logger.info(f"Versione {version or 'latest'} della documentazione {doc_type} recuperata")
            return content

        except Exception as e:
            logger.error(f"Errore nel recupero della versione della documentazione: {str(e)}")
            raise

    async def get_config_version(
        self,
        config_name: str,
        version: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Recupera una versione specifica della configurazione.
        """
        try:
            config = self.config_manager.get_config_version(config_name, version)
            logger.info(f"Versione {version or 'latest'} della configurazione {config_name} recuperata")
            return config

        except ConfigurationError as e:
            logger.error(f"Errore nel recupero della versione della configurazione: {str(e)}")
            raise

    async def validate_sensitive_config(self, required_keys: List[str]) -> bool:
        """
        Verifica la presenza di tutte le configurazioni sensibili richieste.
        """
        try:
            self.config_manager.validate_sensitive_config(required_keys)
            logger.info("Configurazioni sensibili validate con successo")
            return True

        except ConfigurationError as e:
            logger.error(f"Errore nella validazione delle configurazioni sensibili: {str(e)}")
            return False

    async def update_env_variable(self, key: str, value: str) -> None:
        """
        Aggiorna una variabile d'ambiente.
        """
        try:
            self.config_manager.update_env(key, value)
            logger.info(f"Variabile d'ambiente {key} aggiornata con successo")

        except ConfigurationError as e:
            logger.error(f"Errore nell'aggiornamento della variabile d'ambiente: {str(e)}")
            raise

    async def merge_configurations(
        self,
        base_config: Dict[str, Any],
        override_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Unisce due configurazioni.
        """
        try:
            merged = self.config_manager.merge_configs(base_config, override_config)
            logger.info("Configurazioni unite con successo")
            return merged

        except ConfigurationError as e:
            logger.error(f"Errore nella fusione delle configurazioni: {str(e)}")
            raise 