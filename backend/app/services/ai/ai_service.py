from typing import List, Dict, Any, Optional
from langchain.llms import OpenAI
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.vectorstores import FAISS
import spacy
import re
from datetime import datetime
import logging
from ...core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        # Inizializza modelli e componenti
        self.llm = OpenAI(
            temperature=0,
            model_name="gpt-4",
            openai_api_key=settings.OPENAI_API_KEY
        )
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )
        self.nlp = spacy.load("it_core_news_lg")
        
        # Template per l'estrazione di informazioni
        self.info_template = PromptTemplate(
            input_variables=["text"],
            template="""
            Analizza il seguente testo ed estrai le informazioni rilevanti:

            Testo:
            {text}

            Estrai e formatta le seguenti informazioni in formato strutturato:
            1. Date menzionate (formato: YYYY-MM-DD)
            2. Importi monetari (formato: EUR X.XXX,XX)
            3. Nomi di persone
            4. Organizzazioni
            5. Luoghi
            6. Riferimenti normativi
            7. Numeri di protocollo/riferimento

            Rispondi SOLO con le informazioni trovate in formato JSON.
            """
        )
        
        self.summary_template = PromptTemplate(
            input_variables=["text"],
            template="""
            Riassumi il seguente testo in modo conciso ed efficace, evidenziando:
            - Oggetto principale
            - Parti coinvolte
            - Decisioni/conclusioni principali
            - Date rilevanti

            Testo:
            {text}

            Riassunto (max 250 parole):
            """
        )

    async def extract_entities(self, text: str) -> Dict[str, Any]:
        """
        Estrae entità e informazioni strutturate dal testo usando LLM e SpaCy.
        """
        try:
            # Analisi con SpaCy
            doc = self.nlp(text)
            
            # Estrazione base con SpaCy
            entities = {
                "persone": [],
                "organizzazioni": [],
                "luoghi": [],
                "date": [],
                "importi": [],
                "riferimenti": []
            }
            
            # Raccogli entità da SpaCy
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
            entities["importi"].extend(importi)
            
            # Cerca riferimenti normativi
            ref_pattern = r'(?:art\.|articolo)\s+\d+(?:\s+(?:comma|c\.)\s+\d+)?(?:\s+(?:del|della|dello|dell\')\s+[^,\.]+)'
            refs = re.findall(ref_pattern, text, re.IGNORECASE)
            entities["riferimenti"].extend(refs)
            
            # Usa LLM per estrazione avanzata
            chain = LLMChain(llm=self.llm, prompt=self.info_template)
            llm_result = await chain.arun(text=text[:4000])  # Limita lunghezza per token
            
            # Integra risultati LLM con quelli di SpaCy
            try:
                llm_entities = eval(llm_result)
                for key in entities:
                    if key in llm_entities:
                        entities[key].extend(llm_entities[key])
            except:
                logger.warning("Errore nel parsing del risultato LLM")
            
            # Rimuovi duplicati e ordina
            for key in entities:
                entities[key] = sorted(list(set(entities[key])))
            
            return entities
            
        except Exception as e:
            logger.error(f"Errore nell'estrazione delle entità: {str(e)}")
            raise

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Genera l'embedding per un testo usando HuggingFace.
        """
        try:
            # Normalizza il testo
            text = text.replace("\n", " ").strip()
            
            # Genera embedding
            embedding = self.embeddings.embed_query(text)
            return embedding
            
        except Exception as e:
            logger.error(f"Errore nella generazione dell'embedding: {str(e)}")
            raise

    async def semantic_search(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Esegue una ricerca semantica sui documenti usando FAISS.
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
                    "score": float(score),
                    "highlights": self._get_highlights(doc.page_content, query)
                })
                
            return similar_docs
            
        except Exception as e:
            logger.error(f"Errore nella ricerca semantica: {str(e)}")
            raise

    def _get_highlights(
        self,
        text: str,
        query: str,
        context_chars: int = 100
    ) -> List[str]:
        """
        Estrae frammenti di testo rilevanti intorno alle occorrenze della query.
        """
        highlights = []
        try:
            # Implementazione semplificata - da migliorare con NLP
            text_lower = text.lower()
            query_lower = query.lower()
            
            start = 0
            while True:
                pos = text_lower.find(query_lower, start)
                if pos == -1:
                    break
                    
                # Estrai contesto
                highlight_start = max(0, pos - context_chars)
                highlight_end = min(len(text), pos + len(query) + context_chars)
                highlight = text[highlight_start:highlight_end]
                
                # Aggiungi ellipsis se necessario
                if highlight_start > 0:
                    highlight = "..." + highlight
                if highlight_end < len(text):
                    highlight = highlight + "..."
                    
                highlights.append(highlight)
                start = pos + len(query)
                
            return highlights[:3]  # Limita a 3 highlights
            
        except Exception as e:
            logger.error(f"Errore nell'estrazione degli highlights: {str(e)}")
            return []

    async def generate_summary(self, text: str) -> str:
        """
        Genera un riassunto del documento usando LLM.
        """
        try:
            chain = LLMChain(llm=self.llm, prompt=self.summary_template)
            summary = await chain.arun(text=text[:4000])  # Limita lunghezza per token
            return summary.strip()
            
        except Exception as e:
            logger.error(f"Errore nella generazione del riassunto: {str(e)}")
            raise 