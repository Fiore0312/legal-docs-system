from typing import List, Dict, Any, Optional
import pytesseract
from pdf2image import convert_from_path
import spacy
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.document_loaders import PyPDFLoader
from transformers import pipeline
import re
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self):
        # Carica modelli
        self.nlp = spacy.load("it_core_news_lg")
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )
        self.classifier = pipeline(
            "text-classification",
            model="dbmdz/bert-base-italian-uncased",
            return_all_scores=True
        )
        
        # Configurazione text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )

    async def extract_text_from_pdf(self, file_path: str) -> str:
        """
        Estrae il testo da un PDF usando OCR se necessario.
        """
        try:
            # Prima prova a estrarre il testo direttamente
            loader = PyPDFLoader(file_path)
            pages = loader.load_and_split()
            text = "\n\n".join([p.page_content for p in pages])
            
            # Se non c'è testo, usa OCR
            if not text.strip():
                images = convert_from_path(file_path)
                text = ""
                for image in images:
                    text += pytesseract.image_to_string(image, lang='ita') + "\n\n"
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"Errore nell'estrazione del testo da PDF: {str(e)}")
            raise

    async def extract_text_from_image(self, file_path: str) -> str:
        """
        Estrae il testo da un'immagine usando OCR.
        """
        try:
            return pytesseract.image_to_string(file_path, lang='ita')
        except Exception as e:
            logger.error(f"Errore nell'OCR dell'immagine: {str(e)}")
            raise

    async def _create_embedding(self, text: str) -> List[float]:
        """
        Genera l'embedding per un testo.
        """
        try:
            # Normalizza il testo
            text = text.replace("\n", " ").strip()
            
            # Genera embedding
            embeddings = self.embeddings.embed_query(text)
            return embeddings
            
        except Exception as e:
            logger.error(f"Errore nella generazione dell'embedding: {str(e)}")
            raise

    async def _classify_document(self, text: str) -> str:
        """
        Classifica il tipo di documento in base al contenuto.
        """
        try:
            # Estrai le prime 512 tokens per la classificazione
            preview = " ".join(text.split()[:512])
            
            # Classifica
            result = self.classifier(preview)[0]
            
            # Prendi la classe con score più alto
            top_class = max(result, key=lambda x: x['score'])
            return top_class['label']
            
        except Exception as e:
            logger.error(f"Errore nella classificazione del documento: {str(e)}")
            raise

    async def _extract_entities(self, text: str) -> Dict[str, Any]:
        """
        Estrae entità nominate e altre informazioni strutturate dal testo.
        """
        try:
            # Analizza il testo con spaCy
            doc = self.nlp(text)
            
            # Estrai entità
            entities = {
                "persone": [],
                "organizzazioni": [],
                "luoghi": [],
                "date": [],
                "importi": []
            }
            
            # Raccogli entità nominate
            for ent in doc.ents:
                if ent.label_ == "PER":
                    entities["persone"].append(ent.text)
                elif ent.label_ == "ORG":
                    entities["organizzazioni"].append(ent.text)
                elif ent.label_ == "LOC":
                    entities["luoghi"].append(ent.text)
                elif ent.label_ == "DATE":
                    entities["date"].append(ent.text)
                    
            # Cerca importi con regex
            importi_pattern = r'(?:EUR|€)\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)'
            importi = re.findall(importi_pattern, text)
            entities["importi"] = importi
            
            # Rimuovi duplicati e ordina
            for key in entities:
                entities[key] = sorted(list(set(entities[key])))
                
            return entities
            
        except Exception as e:
            logger.error(f"Errore nell'estrazione delle entità: {str(e)}")
            raise

    async def analyze_document(self, file_path: str) -> Dict[str, Any]:
        """
        Analizza completamente un documento estraendo testo, entità e classificazione.
        """
        try:
            # Estrai testo in base al tipo di file
            file_ext = Path(file_path).suffix.lower()
            if file_ext == '.pdf':
                text = await self.extract_text_from_pdf(file_path)
            elif file_ext in ['.jpg', '.jpeg', '.png', '.tiff']:
                text = await self.extract_text_from_image(file_path)
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                    
            # Genera embedding
            embedding = await self._create_embedding(text)
            
            # Classifica documento
            doc_type = await self._classify_document(text)
            
            # Estrai entità
            entities = await self._extract_entities(text)
            
            return {
                "text": text,
                "embedding": embedding,
                "document_type": doc_type,
                "entities": entities
            }
            
        except Exception as e:
            logger.error(f"Errore nell'analisi del documento: {str(e)}")
            raise

    async def search_similar(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Cerca documenti simili usando gli embedding.
        """
        try:
            # Crea database vettoriale temporaneo
            texts = [doc["text"] for doc in documents]
            embeddings = [doc["embedding"] for doc in documents]
            
            db = FAISS.from_embeddings(
                text_embeddings=list(zip(texts, embeddings)),
                embedding=self.embeddings
            )
            
            # Esegui ricerca
            results = db.similarity_search_with_score(query, k=top_k)
            
            # Formatta risultati
            similar_docs = []
            for doc, score in results:
                similar_docs.append({
                    "text": doc.page_content,
                    "score": float(score)
                })
                
            return similar_docs
            
        except Exception as e:
            logger.error(f"Errore nella ricerca di documenti simili: {str(e)}")
            raise 