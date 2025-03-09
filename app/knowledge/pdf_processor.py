from typing import List, Dict, Optional
import os
from pypdf import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.docstore.document import Document
import logging
import traceback

class PDFProcessor:
    def __init__(self, pdf_dir: str = "app/knowledge/data/pdfs"):
        try:
            self.pdf_dir = pdf_dir
            self.embeddings = OpenAIEmbeddings()
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len
            )
            self.vector_store = None

            # Opprett PDF-mappe hvis den ikke eksisterer
            os.makedirs(pdf_dir, exist_ok=True)
            os.makedirs("app/knowledge/data/vector_store", exist_ok=True)
            
            logging.info(f"PDFProcessor initialisert med mappe: {pdf_dir}")
        except Exception as e:
            logging.error(f"Feil ved initialisering av PDFProcessor: {str(e)}")
            logging.error(traceback.format_exc())
            raise

    def process_pdf(self, pdf_path: str) -> List[Document]:
        """Prosesserer en enkelt PDF-fil og returnerer dokumentfragmenter"""
        try:
            logging.info(f"Prosesserer dokument: {pdf_path}")
            # For testing, hvis filen er .txt, les den direkte
            if pdf_path.endswith('.txt'):
                with open(pdf_path, 'r', encoding='utf-8') as f:
                    raw_text = f.read()
                    logging.info(f"Lest {len(raw_text)} tegn fra tekstfil")
            else:
                reader = PdfReader(pdf_path)
                raw_text = ""
                for i, page in enumerate(reader.pages):
                    text = page.extract_text()
                    if text:
                        raw_text += text + "\n"
                logging.info(f"Lest {len(raw_text)} tegn fra PDF med {len(reader.pages)} sider")

            # Del teksten inn i mindre biter
            texts = self.text_splitter.split_text(raw_text)
            logging.info(f"Delt tekst i {len(texts)} fragmenter")

            # Opprett Document-objekter med metadata
            documents = [
                Document(
                    page_content=t,
                    metadata={
                        "source": os.path.basename(pdf_path),
                        "page": i
                    }
                ) for i, t in enumerate(texts)
            ]

            return documents

        except Exception as e:
            logging.error(f"Feil ved prosessering av dokument {pdf_path}: {str(e)}")
            logging.error(traceback.format_exc())
            return []

    def process_all_documents(self) -> None:
        """Prosesserer alle dokumenter i mappen og oppretter en vektorbutikk"""
        try:
            all_documents = []

            # Sjekk om mappen eksisterer og har filer
            if not os.path.exists(self.pdf_dir):
                logging.warning(f"Mappen {self.pdf_dir} eksisterer ikke")
                return

            files = os.listdir(self.pdf_dir)
            if not files:
                logging.warning(f"Ingen filer funnet i {self.pdf_dir}")
                return

            logging.info(f"Fant {len(files)} filer i {self.pdf_dir}")
            for filename in files:
                if filename.endswith(('.pdf', '.txt')):
                    file_path = os.path.join(self.pdf_dir, filename)
                    documents = self.process_pdf(file_path)
                    all_documents.extend(documents)

            if all_documents:
                # Opprett eller oppdater vektorbutikken
                logging.info(f"Oppretter vektorbutikk med {len(all_documents)} dokumentfragmenter")
                self.vector_store = Chroma.from_documents(
                    documents=all_documents,
                    embedding=self.embeddings,
                    persist_directory="app/knowledge/data/vector_store"
                )
                logging.info(f"Prosessert {len(all_documents)} dokumentfragmenter")
            else:
                logging.warning("Ingen dokumenter ble funnet eller prosessert")

        except Exception as e:
            logging.error(f"Feil ved prosessering av dokumenter: {str(e)}")
            logging.error(traceback.format_exc())

    async def search_documents(self, query: str, k: int = 3) -> List[Dict]:
        """Søk i dokumentene etter relevant informasjon"""
        try:
            logging.info(f"Søker etter: {query}")
            if not self.vector_store:
                logging.info("Ingen vektorbutikk funnet, prosesserer dokumenter")
                self.process_all_documents()

            if not self.vector_store:
                logging.warning("Kunne ikke opprette vektorbutikk")
                return []

            # Utfør semantisk søk
            results = self.vector_store.similarity_search_with_score(query, k=k)
            logging.info(f"Fant {len(results)} resultater")

            # Formater resultatene
            formatted_results = []
            for doc, score in results:
                formatted_results.append({
                    "content": doc.page_content,
                    "source": doc.metadata["source"],
                    "page": doc.metadata["page"],
                    "relevance_score": float(score)  # Konverter direkte til float
                })

            return formatted_results

        except Exception as e:
            logging.error(f"Feil ved søk i dokumenter: {str(e)}")
            logging.error(traceback.format_exc())
            return []

    def get_document_summary(self) -> Dict[str, int]:
        """Returner en oversikt over prosesserte dokumenter"""
        try:
            summary = {}
            if os.path.exists(self.pdf_dir):
                for filename in os.listdir(self.pdf_dir):
                    if filename.endswith(('.pdf', '.txt')):
                        file_path = os.path.join(self.pdf_dir, filename)
                        if filename.endswith('.pdf'):
                            reader = PdfReader(file_path)
                            summary[filename] = len(reader.pages)
                        else:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                lines = f.readlines()
                                summary[filename] = len(lines)
            return summary
        except Exception as e:
            logging.error(f"Feil ved generering av dokumentoversikt: {str(e)}")
            logging.error(traceback.format_exc())
            return {}
