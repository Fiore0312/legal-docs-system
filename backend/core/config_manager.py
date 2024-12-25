from typing import Dict, Any, Optional
import os
import yaml
import json
import logging
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel, ValidationError
from dotenv import load_dotenv, set_key

logger = logging.getLogger(__name__)

class ConfigurationError(Exception):
    """Errore personalizzato per problemi di configurazione."""
    pass

class ConfigManager:
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir = self.config_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        self.env_file = Path(".env")
        load_dotenv()

    def load_config(self, config_name: str) -> Dict[str, Any]:
        """
        Carica una configurazione da file YAML.
        """
        try:
            config_path = self.config_dir / f"{config_name}.yaml"
            if not config_path.exists():
                raise ConfigurationError(f"File di configurazione {config_name} non trovato")
            
            with config_path.open("r") as f:
                config = yaml.safe_load(f)
            
            logger.info(f"Configurazione {config_name} caricata con successo")
            return config

        except Exception as e:
            logger.error(f"Errore nel caricamento della configurazione {config_name}: {str(e)}")
            raise ConfigurationError(str(e))

    def save_config(self, config_name: str, config_data: Dict[str, Any]) -> None:
        """
        Salva una configurazione in file YAML.
        """
        try:
            config_path = self.config_dir / f"{config_name}.yaml"
            
            # Backup configurazione esistente
            if config_path.exists():
                backup_path = self.backup_dir / f"{config_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.yaml"
                with config_path.open("r") as src, backup_path.open("w") as dst:
                    dst.write(src.read())
            
            # Salva nuova configurazione
            with config_path.open("w") as f:
                yaml.dump(config_data, f, default_flow_style=False)
            
            logger.info(f"Configurazione {config_name} salvata con successo")

        except Exception as e:
            logger.error(f"Errore nel salvataggio della configurazione {config_name}: {str(e)}")
            raise ConfigurationError(str(e))

    def validate_config(self, config_data: Dict[str, Any], schema_model: BaseModel) -> None:
        """
        Valida una configurazione contro uno schema Pydantic.
        """
        try:
            schema_model(**config_data)
            logger.info("Validazione configurazione completata con successo")
        except ValidationError as e:
            logger.error(f"Errore nella validazione della configurazione: {str(e)}")
            raise ConfigurationError(str(e))

    def update_env(self, key: str, value: str) -> None:
        """
        Aggiorna una variabile d'ambiente nel file .env.
        """
        try:
            if not self.env_file.exists():
                self.env_file.touch()
            
            set_key(str(self.env_file), key, value)
            os.environ[key] = value
            logger.info(f"Variabile d'ambiente {key} aggiornata con successo")

        except Exception as e:
            logger.error(f"Errore nell'aggiornamento della variabile d'ambiente {key}: {str(e)}")
            raise ConfigurationError(str(e))

    def get_config_schema(self, config_name: str) -> Dict[str, Any]:
        """
        Recupera lo schema di una configurazione.
        """
        try:
            schema_path = self.config_dir / f"{config_name}_schema.yaml"
            if not schema_path.exists():
                raise ConfigurationError(f"Schema di configurazione {config_name} non trovato")
            
            with schema_path.open("r") as f:
                schema = yaml.safe_load(f)
            
            return schema

        except Exception as e:
            logger.error(f"Errore nel recupero dello schema {config_name}: {str(e)}")
            raise ConfigurationError(str(e))

    def merge_configs(self, base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Unisce due configurazioni, con override_config che ha la precedenza.
        """
        def deep_merge(source: Dict[str, Any], destination: Dict[str, Any]) -> Dict[str, Any]:
            for key, value in source.items():
                if key in destination:
                    if isinstance(value, dict) and isinstance(destination[key], dict):
                        destination[key] = deep_merge(value, destination[key])
                    else:
                        destination[key] = value
                else:
                    destination[key] = value
            return destination

        try:
            result = base_config.copy()
            return deep_merge(override_config, result)
        except Exception as e:
            logger.error(f"Errore nella fusione delle configurazioni: {str(e)}")
            raise ConfigurationError(str(e))

    def get_sensitive_config(self) -> Dict[str, str]:
        """
        Recupera le configurazioni sensibili dal file .env.
        """
        try:
            if not self.env_file.exists():
                return {}
            
            sensitive_config = {}
            with self.env_file.open("r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        key, value = line.split("=", 1)
                        sensitive_config[key.strip()] = value.strip()
            
            return sensitive_config

        except Exception as e:
            logger.error(f"Errore nel recupero delle configurazioni sensibili: {str(e)}")
            raise ConfigurationError(str(e))

    def validate_sensitive_config(self, required_keys: List[str]) -> None:
        """
        Verifica che tutte le configurazioni sensibili richieste siano presenti.
        """
        try:
            sensitive_config = self.get_sensitive_config()
            missing_keys = [key for key in required_keys if key not in sensitive_config]
            
            if missing_keys:
                raise ConfigurationError(f"Configurazioni sensibili mancanti: {', '.join(missing_keys)}")
            
            logger.info("Validazione configurazioni sensibili completata con successo")

        except Exception as e:
            logger.error(f"Errore nella validazione delle configurazioni sensibili: {str(e)}")
            raise ConfigurationError(str(e))

    def get_config_version(self, config_name: str, version: Optional[str] = None) -> Dict[str, Any]:
        """
        Recupera una versione specifica di una configurazione.
        """
        try:
            if version:
                version_path = self.backup_dir / f"{config_name}_{version}.yaml"
                if not version_path.exists():
                    raise ConfigurationError(f"Versione {version} non trovata per {config_name}")
                
                with version_path.open("r") as f:
                    return yaml.safe_load(f)
            
            # Lista tutte le versioni
            versions = []
            for file in self.backup_dir.glob(f"{config_name}_*.yaml"):
                version = file.stem.split("_")[-1]
                versions.append({
                    "version": version,
                    "date": datetime.strptime(version, "%Y%m%d_%H%M%S"),
                    "path": file
                })
            
            if not versions:
                raise ConfigurationError(f"Nessuna versione trovata per {config_name}")
            
            # Recupera l'ultima versione
            latest = max(versions, key=lambda x: x["date"])
            with latest["path"].open("r") as f:
                return yaml.safe_load(f)

        except Exception as e:
            logger.error(f"Errore nel recupero della versione: {str(e)}")
            raise ConfigurationError(str(e)) 