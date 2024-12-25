import os
import sys
import json
import time
import logging
import requests
import psycopg2
import smtplib
import redis
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/system_test.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class SystemTester:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.api_url = f"{self.base_url}/api/v1"
        self.test_results = []
        self.test_user = {
            "email": "test@example.com",
            "password": "Test123!",
            "first_name": "Test",
            "last_name": "User"
        }
        self.access_token = None

    def log_test(self, test_name: str, success: bool, error: str = None, performance: Dict = None):
        """Registra risultato test"""
        result = {
            "test": test_name,
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "error": error,
            "performance": performance
        }
        self.test_results.append(result)
        
        if success:
            logger.info(f"✓ {test_name} completato con successo")
            if performance:
                logger.info(f"  Performance: {json.dumps(performance)}")
        else:
            logger.error(f"✗ {test_name} fallito: {error}")

    def test_database(self) -> bool:
        """Test connessione database"""
        try:
            start_time = time.time()
            conn = psycopg2.connect(os.getenv("DATABASE_URL"))
            cur = conn.cursor()
            
            # Test query
            cur.execute("SELECT version();")
            version = cur.fetchone()
            
            # Test pgvector
            cur.execute("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector');")
            has_vector = cur.fetchone()[0]
            
            cur.close()
            conn.close()
            
            elapsed = time.time() - start_time
            self.log_test(
                "Database Connection",
                True,
                performance={
                    "connection_time": f"{elapsed:.2f}s",
                    "has_vector": has_vector
                }
            )
            return True
        
        except Exception as e:
            self.log_test("Database Connection", False, str(e))
            return False

    def test_auth_system(self) -> bool:
        """Test sistema autenticazione"""
        try:
            # Registrazione
            start_time = time.time()
            response = requests.post(
                f"{self.api_url}/auth/register",
                json=self.test_user
            )
            register_time = time.time() - start_time
            
            if response.status_code not in [201, 409]:  # 409 se utente esiste
                raise Exception(f"Registrazione fallita: {response.text}")
            
            # Login
            start_time = time.time()
            response = requests.post(
                f"{self.api_url}/auth/login",
                data={
                    "username": self.test_user["email"],
                    "password": self.test_user["password"]
                }
            )
            login_time = time.time() - start_time
            
            if response.status_code != 200:
                raise Exception(f"Login fallito: {response.text}")
            
            self.access_token = response.json()["access_token"]
            
            self.log_test(
                "Authentication System",
                True,
                performance={
                    "register_time": f"{register_time:.2f}s",
                    "login_time": f"{login_time:.2f}s"
                }
            )
            return True
        
        except Exception as e:
            self.log_test("Authentication System", False, str(e))
            return False

    def test_email_system(self) -> bool:
        """Test sistema email"""
        try:
            start_time = time.time()
            smtp = smtplib.SMTP(os.getenv("SMTP_SERVER"), int(os.getenv("SMTP_PORT")))
            smtp.starttls()
            smtp.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASSWORD"))
            smtp.quit()
            
            elapsed = time.time() - start_time
            self.log_test(
                "Email System",
                True,
                performance={"connection_time": f"{elapsed:.2f}s"}
            )
            return True
        
        except Exception as e:
            self.log_test("Email System", False, str(e))
            return False

    def test_ai_integration(self) -> bool:
        """Test integrazione AI"""
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Test embedding
            start_time = time.time()
            response = requests.post(
                f"{self.api_url}/ai/embed",
                json={"text": "Questo è un test di embedding"},
                headers=headers
            )
            embed_time = time.time() - start_time
            
            if response.status_code != 200:
                raise Exception(f"Embedding fallito: {response.text}")
            
            # Test completamento
            start_time = time.time()
            response = requests.post(
                f"{self.api_url}/ai/complete",
                json={"prompt": "Analizza questo testo: test"},
                headers=headers
            )
            complete_time = time.time() - start_time
            
            if response.status_code != 200:
                raise Exception(f"Completamento fallito: {response.text}")
            
            self.log_test(
                "AI Integration",
                True,
                performance={
                    "embed_time": f"{embed_time:.2f}s",
                    "complete_time": f"{complete_time:.2f}s"
                }
            )
            return True
        
        except Exception as e:
            self.log_test("AI Integration", False, str(e))
            return False

    def test_document_upload(self) -> bool:
        """Test upload documento"""
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            test_file = Path("tests/data/test_document.pdf")
            
            if not test_file.exists():
                raise Exception("File di test non trovato")
            
            start_time = time.time()
            with open(test_file, "rb") as f:
                response = requests.post(
                    f"{self.api_url}/documenti",
                    files={"file": f},
                    data={"tipo": "test", "descrizione": "Documento di test"},
                    headers=headers
                )
            
            upload_time = time.time() - start_time
            
            if response.status_code != 201:
                raise Exception(f"Upload fallito: {response.text}")
            
            self.document_id = response.json()["id"]
            
            self.log_test(
                "Document Upload",
                True,
                performance={
                    "upload_time": f"{upload_time:.2f}s",
                    "file_size": f"{test_file.stat().st_size / 1024:.2f}KB"
                }
            )
            return True
        
        except Exception as e:
            self.log_test("Document Upload", False, str(e))
            return False

    def test_ocr(self) -> bool:
        """Test OCR"""
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            start_time = time.time()
            response = requests.post(
                f"{self.api_url}/ai/{self.document_id}/ocr",
                headers=headers
            )
            ocr_time = time.time() - start_time
            
            if response.status_code != 200:
                raise Exception(f"OCR fallito: {response.text}")
            
            text_length = len(response.json()["text"])
            
            self.log_test(
                "OCR Processing",
                True,
                performance={
                    "processing_time": f"{ocr_time:.2f}s",
                    "text_length": text_length
                }
            )
            return True
        
        except Exception as e:
            self.log_test("OCR Processing", False, str(e))
            return False

    def test_semantic_search(self) -> bool:
        """Test ricerca semantica"""
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            start_time = time.time()
            response = requests.get(
                f"{self.api_url}/ai/search",
                params={"query": "test", "limit": 10},
                headers=headers
            )
            search_time = time.time() - start_time
            
            if response.status_code != 200:
                raise Exception(f"Ricerca fallita: {response.text}")
            
            results = response.json()
            
            self.log_test(
                "Semantic Search",
                True,
                performance={
                    "search_time": f"{search_time:.2f}s",
                    "results_count": len(results)
                }
            )
            return True
        
        except Exception as e:
            self.log_test("Semantic Search", False, str(e))
            return False

    def test_entity_extraction(self) -> bool:
        """Test estrazione entità"""
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            start_time = time.time()
            response = requests.post(
                f"{self.api_url}/ai/{self.document_id}/extract-entities",
                headers=headers
            )
            extract_time = time.time() - start_time
            
            if response.status_code != 200:
                raise Exception(f"Estrazione fallita: {response.text}")
            
            entities = response.json()
            
            self.log_test(
                "Entity Extraction",
                True,
                performance={
                    "extraction_time": f"{extract_time:.2f}s",
                    "entities_count": len(entities)
                }
            )
            return True
        
        except Exception as e:
            self.log_test("Entity Extraction", False, str(e))
            return False

    def test_report_generation(self) -> bool:
        """Test generazione report"""
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            start_time = time.time()
            response = requests.post(
                f"{self.api_url}/documenti/{self.document_id}/report",
                headers=headers
            )
            generate_time = time.time() - start_time
            
            if response.status_code != 200:
                raise Exception(f"Generazione report fallita: {response.text}")
            
            self.log_test(
                "Report Generation",
                True,
                performance={"generation_time": f"{generate_time:.2f}s"}
            )
            return True
        
        except Exception as e:
            self.log_test("Report Generation", False, str(e))
            return False

    def test_vector_store(self) -> bool:
        """Test vector store"""
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Test inserimento
            start_time = time.time()
            response = requests.post(
                f"{self.api_url}/ai/vectors",
                json={
                    "text": "test vector store",
                    "metadata": {"type": "test"}
                },
                headers=headers
            )
            insert_time = time.time() - start_time
            
            if response.status_code != 201:
                raise Exception(f"Inserimento vector fallito: {response.text}")
            
            # Test ricerca
            start_time = time.time()
            response = requests.get(
                f"{self.api_url}/ai/vectors/search",
                params={"query": "test", "limit": 5},
                headers=headers
            )
            search_time = time.time() - start_time
            
            if response.status_code != 200:
                raise Exception(f"Ricerca vector fallita: {response.text}")
            
            self.log_test(
                "Vector Store",
                True,
                performance={
                    "insert_time": f"{insert_time:.2f}s",
                    "search_time": f"{search_time:.2f}s"
                }
            )
            return True
        
        except Exception as e:
            self.log_test("Vector Store", False, str(e))
            return False

    def test_cache(self) -> bool:
        """Test sistema cache"""
        try:
            redis_client = redis.Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", 6379)),
                db=0
            )
            
            # Test scrittura
            start_time = time.time()
            redis_client.set("test_key", "test_value", ex=60)
            write_time = time.time() - start_time
            
            # Test lettura
            start_time = time.time()
            value = redis_client.get("test_key")
            read_time = time.time() - start_time
            
            if not value:
                raise Exception("Lettura cache fallita")
            
            self.log_test(
                "Cache System",
                True,
                performance={
                    "write_time": f"{write_time:.2f}s",
                    "read_time": f"{read_time:.2f}s"
                }
            )
            return True
        
        except Exception as e:
            self.log_test("Cache System", False, str(e))
            return False

    def test_rate_limiting(self) -> bool:
        """Test rate limiting"""
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            results = []
            
            start_time = time.time()
            for i in range(10):
                response = requests.get(
                    f"{self.api_url}/health",
                    headers=headers
                )
                results.append(response.status_code)
                time.sleep(0.1)
            
            elapsed = time.time() - start_time
            
            # Verifica se alcuni richieste sono state limitate
            limited = any(code == 429 for code in results)
            
            self.log_test(
                "Rate Limiting",
                True,
                performance={
                    "total_time": f"{elapsed:.2f}s",
                    "requests": len(results),
                    "limited_requests": sum(1 for code in results if code == 429)
                }
            )
            return True
        
        except Exception as e:
            self.log_test("Rate Limiting", False, str(e))
            return False

    def generate_report(self) -> Dict[str, Any]:
        """Genera report finale dei test"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for test in self.test_results if test["success"])
        failed_tests = total_tests - passed_tests
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": f"{(passed_tests/total_tests)*100:.2f}%"
            },
            "results": self.test_results
        }
        
        # Salva report
        report_file = Path("logs/test_report.json")
        report_file.parent.mkdir(exist_ok=True)
        report_file.write_text(json.dumps(report, indent=2))
        
        return report

    def run_all_tests(self) -> bool:
        """Esegue tutti i test"""
        logger.info("Avvio test di sistema...")
        
        # Test di Base
        if not self.test_database():
            logger.error("Test database fallito. Interruzione.")
            return False
        
        if not self.test_auth_system():
            logger.error("Test autenticazione fallito. Interruzione.")
            return False
        
        if not self.test_email_system():
            logger.error("Test email fallito. Interruzione.")
            return False
        
        if not self.test_ai_integration():
            logger.error("Test AI fallito. Interruzione.")
            return False
        
        # Test Funzionalità Core
        if not self.test_document_upload():
            logger.error("Test upload fallito. Interruzione.")
            return False
        
        if not self.test_ocr():
            logger.error("Test OCR fallito. Interruzione.")
            return False
        
        if not self.test_semantic_search():
            logger.error("Test ricerca fallito. Interruzione.")
            return False
        
        if not self.test_entity_extraction():
            logger.error("Test estrazione entità fallito. Interruzione.")
            return False
        
        if not self.test_report_generation():
            logger.error("Test report fallito. Interruzione.")
            return False
        
        # Test Integrazioni
        if not self.test_vector_store():
            logger.error("Test vector store fallito. Interruzione.")
            return False
        
        if not self.test_cache():
            logger.error("Test cache fallito. Interruzione.")
            return False
        
        if not self.test_rate_limiting():
            logger.error("Test rate limiting fallito. Interruzione.")
            return False
        
        # Genera report finale
        report = self.generate_report()
        logger.info("\nReport Finale:")
        logger.info(f"Test totali: {report['summary']['total_tests']}")
        logger.info(f"Test passati: {report['summary']['passed_tests']}")
        logger.info(f"Test falliti: {report['summary']['failed_tests']}")
        logger.info(f"Tasso successo: {report['summary']['success_rate']}")
        
        return report['summary']['failed_tests'] == 0

if __name__ == "__main__":
    tester = SystemTester()
    success = tester.run_all_tests()
    
    if success:
        logger.info("\n✓ Tutti i test completati con successo. Il sistema è pronto per il lancio.")
        sys.exit(0)
    else:
        logger.error("\n✗ Alcuni test sono falliti. Correggere gli errori prima del lancio.")
        sys.exit(1) 