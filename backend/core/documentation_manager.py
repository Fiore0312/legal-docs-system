from typing import Dict, List, Optional, Any
import os
import yaml
import json
import logging
from pathlib import Path
from datetime import datetime
import inspect
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
import markdown2
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class DocumentationManager:
    def __init__(self, app: FastAPI, docs_dir: str = "docs"):
        self.app = app
        self.docs_dir = Path(docs_dir)
        self.docs_dir.mkdir(parents=True, exist_ok=True)
        self.version_dir = self.docs_dir / "versions"
        self.version_dir.mkdir(exist_ok=True)

    def generate_api_docs(self) -> str:
        """
        Genera la documentazione API da FastAPI.
        """
        try:
            openapi_schema = get_openapi(
                title=self.app.title,
                version=self.app.version,
                description=self.app.description,
                routes=self.app.routes
            )

            # Converti OpenAPI in Markdown
            markdown_content = "# API Reference\n\n"
            
            # Info base
            markdown_content += f"## {openapi_schema['info']['title']}\n"
            markdown_content += f"Version: {openapi_schema['info']['version']}\n\n"
            markdown_content += f"{openapi_schema['info']['description']}\n\n"
            
            # Endpoints
            markdown_content += "## Endpoints\n\n"
            for path, path_data in openapi_schema["paths"].items():
                for method, operation in path_data.items():
                    markdown_content += f"### {method.upper()} {path}\n\n"
                    markdown_content += f"{operation.get('description', '')}\n\n"
                    
                    # Parameters
                    if operation.get("parameters"):
                        markdown_content += "#### Parameters\n\n"
                        for param in operation["parameters"]:
                            markdown_content += f"- `{param['name']}` ({param['in']}): {param.get('description', '')}\n"
                        markdown_content += "\n"
                    
                    # Request Body
                    if "requestBody" in operation:
                        markdown_content += "#### Request Body\n\n"
                        content = operation["requestBody"]["content"]
                        for content_type, schema_data in content.items():
                            markdown_content += f"Content-Type: `{content_type}`\n\n"
                            if "schema" in schema_data:
                                markdown_content += "```json\n"
                                markdown_content += json.dumps(schema_data["schema"], indent=2)
                                markdown_content += "\n```\n\n"
                    
                    # Responses
                    markdown_content += "#### Responses\n\n"
                    for status_code, response in operation["responses"].items():
                        markdown_content += f"**{status_code}**: {response.get('description', '')}\n\n"
                        if "content" in response:
                            for content_type, schema_data in response["content"].items():
                                if "schema" in schema_data:
                                    markdown_content += "```json\n"
                                    markdown_content += json.dumps(schema_data["schema"], indent=2)
                                    markdown_content += "\n```\n\n"
            
            # Salva la documentazione
            api_docs_path = self.docs_dir / "api_reference.md"
            api_docs_path.write_text(markdown_content)
            
            # Versioning
            version_path = self.version_dir / f"api_reference_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            version_path.write_text(markdown_content)
            
            logger.info("Documentazione API generata con successo")
            return markdown_content

        except Exception as e:
            logger.error(f"Errore nella generazione della documentazione API: {str(e)}")
            raise

    def generate_setup_guide(self, config_schema: Dict[str, Any]) -> str:
        """
        Genera la guida di setup dal schema di configurazione.
        """
        try:
            markdown_content = "# Setup Guide\n\n"
            markdown_content += "## Requisiti di Sistema\n\n"
            markdown_content += "- Python 3.9+\n"
            markdown_content += "- PostgreSQL 15+ con pgvector\n"
            markdown_content += "- Tesseract OCR\n\n"
            
            markdown_content += "## Configurazione\n\n"
            for section, settings in config_schema.items():
                markdown_content += f"### {section}\n\n"
                if isinstance(settings, dict):
                    for key, value in settings.items():
                        markdown_content += f"#### {key}\n"
                        if isinstance(value, dict):
                            markdown_content += "```yaml\n"
                            markdown_content += yaml.dump({key: value}, default_flow_style=False)
                            markdown_content += "```\n\n"
                        else:
                            markdown_content += f"- Valore di default: `{value}`\n\n"
            
            # Salva la guida
            setup_guide_path = self.docs_dir / "setup_guide.md"
            setup_guide_path.write_text(markdown_content)
            
            logger.info("Guida di setup generata con successo")
            return markdown_content

        except Exception as e:
            logger.error(f"Errore nella generazione della guida di setup: {str(e)}")
            raise

    def generate_agent_instructions(self, capabilities: List[str], commands: List[Dict[str, Any]]) -> str:
        """
        Genera le istruzioni per l'agente.
        """
        try:
            markdown_content = "# Agent Instructions\n\n"
            
            # Capabilities
            markdown_content += "## Capabilities\n\n"
            for capability in capabilities:
                markdown_content += f"- {capability}\n"
            markdown_content += "\n"
            
            # Commands
            markdown_content += "## Available Commands\n\n"
            for command in commands:
                markdown_content += f"### {command['name']}\n\n"
                markdown_content += f"{command.get('description', '')}\n\n"
                
                if "parameters" in command:
                    markdown_content += "#### Parameters\n\n"
                    for param in command["parameters"]:
                        markdown_content += f"- `{param['name']}` ({param['type']}): {param.get('description', '')}\n"
                    markdown_content += "\n"
                
                if "example" in command:
                    markdown_content += "#### Example\n\n"
                    markdown_content += "```python\n"
                    markdown_content += command["example"]
                    markdown_content += "\n```\n\n"
            
            # Salva le istruzioni
            instructions_path = self.docs_dir / "agent_instructions.md"
            instructions_path.write_text(markdown_content)
            
            logger.info("Istruzioni agente generate con successo")
            return markdown_content

        except Exception as e:
            logger.error(f"Errore nella generazione delle istruzioni agente: {str(e)}")
            raise

    def update_documentation(self, doc_type: str, content: str) -> None:
        """
        Aggiorna un documento esistente.
        """
        try:
            doc_path = self.docs_dir / f"{doc_type}.md"
            if not doc_path.exists():
                raise FileNotFoundError(f"Documento {doc_type} non trovato")
            
            # Backup versione precedente
            version_path = self.version_dir / f"{doc_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            version_path.write_text(doc_path.read_text())
            
            # Aggiorna documento
            doc_path.write_text(content)
            logger.info(f"Documento {doc_type} aggiornato con successo")

        except Exception as e:
            logger.error(f"Errore nell'aggiornamento della documentazione: {str(e)}")
            raise

    def read_documentation(self, doc_type: str) -> str:
        """
        Legge un documento esistente.
        """
        try:
            doc_path = self.docs_dir / f"{doc_type}.md"
            if not doc_path.exists():
                raise FileNotFoundError(f"Documento {doc_type} non trovato")
            
            return doc_path.read_text()

        except Exception as e:
            logger.error(f"Errore nella lettura della documentazione: {str(e)}")
            raise

    def parse_markdown(self, content: str) -> Dict[str, Any]:
        """
        Converte Markdown in struttura dati.
        """
        try:
            html = markdown2.markdown(content, extras=["metadata", "tables", "fenced-code-blocks"])
            
            # Estrai sezioni
            sections = {}
            current_section = None
            current_content = []
            
            for line in content.split("\n"):
                if line.startswith("#"):
                    if current_section:
                        sections[current_section] = "\n".join(current_content)
                        current_content = []
                    current_section = line.strip("# ")
                else:
                    current_content.append(line)
            
            if current_section:
                sections[current_section] = "\n".join(current_content)
            
            return {
                "metadata": html.metadata,
                "sections": sections,
                "html": html
            }

        except Exception as e:
            logger.error(f"Errore nel parsing del Markdown: {str(e)}")
            raise

    def get_documentation_version(self, doc_type: str, version: Optional[str] = None) -> str:
        """
        Recupera una versione specifica della documentazione.
        """
        try:
            if version:
                version_path = self.version_dir / f"{doc_type}_{version}.md"
                if not version_path.exists():
                    raise FileNotFoundError(f"Versione {version} non trovata per {doc_type}")
                return version_path.read_text()
            
            # Lista tutte le versioni
            versions = []
            for file in self.version_dir.glob(f"{doc_type}_*.md"):
                version = file.stem.split("_")[-1]
                versions.append({
                    "version": version,
                    "date": datetime.strptime(version, "%Y%m%d_%H%M%S"),
                    "path": file
                })
            
            if not versions:
                raise FileNotFoundError(f"Nessuna versione trovata per {doc_type}")
            
            # Recupera l'ultima versione
            latest = max(versions, key=lambda x: x["date"])
            return latest["path"].read_text()

        except Exception as e:
            logger.error(f"Errore nel recupero della versione: {str(e)}")
            raise 