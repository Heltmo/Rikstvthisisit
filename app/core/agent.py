from typing import Dict, List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from ..config.settings import settings
from ..knowledge.pdf_processor import PDFProcessor
import json
import logging
import os
import traceback

class RiksTVAgent:
    def __init__(self):
        try:
            self.llm = ChatOpenAI(
                temperature=settings.TEMPERATURE,
                model_name=settings.MODEL_NAME,
                max_tokens=settings.MAX_TOKENS,
                api_key=settings.OPENAI_API_KEY
            )

            # Initialiser chat-historikk med system-melding
            self.system_prompt = """Du er en AI-kundeserviceassistent for RiksTV. Din oppgave er å gi klare, presise og nyttige svar på spørsmål om TV-tjenester, signalproblemer, dekodere, kanaler, abonnementer og tilkobling.

VIKTIGE RETNINGSLINJER:
1. **Svar kort og direkte** – Unngå unødvendig lange forklaringer.
2. **Bruk punktlister for steg-for-steg veiledning.**
3. **Tilpass svarene til spørsmålet** – Hvis spørsmålet er enkelt, svar enkelt.
4. **Referer til dokumentasjon om nødvendig** – Hent informasjon fra kunnskapsbasen og relevante PDF-dokumenter.
5. **Eskaler hvis problemet krever menneskelig kundeservice** – Bruk formuleringen: 'Dette krever videre hjelp fra kundeservice. Ring 21022713 for assistanse.'"""

            self.chat_history = [
                SystemMessage(content=self.system_prompt)
            ]

            self.prompt = ChatPromptTemplate.from_messages([
                ("system", self.system_prompt),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}")
            ])

            self.chain = self.prompt | self.llm | StrOutputParser()

            self.pdf_processor = PDFProcessor()
            self.active_sessions = {}
            self.load_knowledge_base()
            
            logging.info("RiksTVAgent initialisert vellykket")
        except Exception as e:
            logging.error(f"Feil ved initialisering av RiksTVAgent: {str(e)}")
            logging.error(traceback.format_exc())
            raise

    def load_knowledge_base(self):
        """Last inn kunnskapsbasen fra JSON-filer og dokumenter"""
        try:
            # Bruk hardkodede data som fallback
            self.troubleshooting_data = {
                "signal": {
                    "common_issues": [
                        {
                            "problem": "Ingen TV-signal",
                            "solutions": [
                                {
                                    "description": "Sjekk at dekoderen er slått på",
                                    "details": "Se etter at strømlampen lyser på dekoderen"
                                },
                                {
                                    "description": "Kontroller alle kabeltilkoblinger",
                                    "details": "Sjekk både strømkabel, HDMI-kabel og antennekabel"
                                },
                                {
                                    "description": "Restart dekoderen",
                                    "details": "Trekk ut strømkabelen, vent 30 sekunder, sett den inn igjen"
                                }
                            ]
                        }
                    ]
                },
                "decoder": {
                    "common_issues": [
                        {
                            "problem": "Dekoder starter ikke",
                            "solutions": [
                                {
                                    "description": "Sjekk strømtilkobling",
                                    "details": "Kontroller at strømkabelen er ordentlig tilkoblet"
                                },
                                {
                                    "description": "Prøv annen stikkontakt",
                                    "details": "Test dekoderen i en annen stikkontakt"
                                },
                                {
                                    "description": "Utfør hard reset",
                                    "details": "Hold inne power-knappen i 10 sekunder"
                                }
                            ]
                        }
                    ]
                }
            }
            
            self.faq_data = {
                "general": [
                    {
                        "question": "Hva er RiksTV?",
                        "answer": "RiksTV er en norsk TV-distributør som tilbyr TV-kanaler og strømmetjenester via det digitale bakkenettet og internett."
                    },
                    {
                        "question": "Hvordan kontakter jeg kundeservice?",
                        "answer": "Du kan kontakte RiksTV kundeservice på telefon 210 00 210 (hverdager 08-20, lørdag 09-17) eller via chat på rikstv.no."
                    }
                ],
                "subscription": [
                    {
                        "question": "Hvordan endrer jeg abonnementet mitt?",
                        "answer": "Du kan endre abonnementet ditt ved å logge inn på Min Side på rikstv.no eller kontakte kundeservice."
                    }
                ]
            }

            # Prosesser dokumenter
            logging.info("Starter prosessering av dokumenter")
            self.pdf_processor.process_all_documents()
            logging.info("Dokumenter prosessert vellykket")

        except Exception as e:
            logging.error(f"Kunne ikke laste kunnskapsbase: {str(e)}")
            logging.error(traceback.format_exc())
            self.troubleshooting_data = {}
            self.faq_data = {}

    def get_session_history(self, session_id: str) -> List:
        """Hent samtalehistorikk for en bestemt sesjon"""
        if session_id not in self.active_sessions:
            # Start ny sesjon med velkomstmelding
            self.active_sessions[session_id] = [
                SystemMessage(content=self.system_prompt),
                AIMessage(content="Hei! Jeg er RiksTVs digitale assistent. Hvordan kan jeg hjelpe deg i dag?")
            ]
        return self.active_sessions[session_id]

    async def handle_query(self, user_input: str, session_id: str = "default") -> Dict:
        """Hovedmetode for å håndtere kundehenvendelser"""
        try:
            logging.info(f"Håndterer spørsmål: {user_input}")
            category = self.identify_problem_category(user_input)
            logging.info(f"Identifisert kategori: {category}")

            # Hent samtalehistorikk for sesjonen
            session_history = self.get_session_history(session_id)

            # Søk i dokumenter etter relevant informasjon
            logging.info("Søker i dokumenter")
            try:
                doc_results = await self.pdf_processor.search_documents(user_input)
                logging.info(f"Fant {len(doc_results)} relevante dokumenter")
            except Exception as e:
                logging.error(f"Feil ved søk i dokumenter: {str(e)}")
                logging.error(traceback.format_exc())
                doc_results = []

            # Sjekk om vi trenger mer informasjon
            if len(user_input.split()) < 3:
                response = "Kan du beskrive problemet ditt litt mer detaljert? Dette vil hjelpe meg å gi deg best mulig støtte."
                self._update_session_history(session_id, user_input, response)
                return {
                    "response": response,
                    "category": category,
                    "needs_human": False,
                    "steps": None,
                    "sources": []
                }

            # Legg til dokumentkontekst i input
            context = "\n\nRelevant dokumentasjon:\n" + "\n".join([r["content"] for r in doc_results]) if doc_results else ""
            full_input = user_input + context
            logging.info(f"Full input med kontekst: {full_input[:100]}...")

            # Generer svar ved hjelp av LLM med samtalehistorikk
            logging.info("Genererer svar med LLM")
            try:
                response = self.chain.invoke({
                    "chat_history": session_history,
                    "input": full_input
                })
                logging.info(f"Generert svar: {response[:100]}...")
            except Exception as e:
                logging.error(f"Feil ved generering av svar: {str(e)}")
                logging.error(traceback.format_exc())
                response = "Beklager, jeg opplevde en teknisk feil. Vennligst prøv igjen eller kontakt kundeservice."

            # Oppdater samtalehistorikk
            self._update_session_history(session_id, user_input, response)

            # Vurder om saken bør eskaleres
            needs_human = self._should_escalate(user_input, response)

            # Hent relevante trinn fra troubleshooting data
            steps = self._get_troubleshooting_steps(category)

            return {
                "response": response,
                "category": category,
                "needs_human": needs_human,
                "steps": steps,
                "sources": [{"source": r["source"], "page": r["page"]} for r in doc_results]
            }

        except Exception as e:
            logging.error(f"Feil ved håndtering av henvendelse: {str(e)}")
            logging.error(traceback.format_exc())
            return {
                "response": "Beklager, jeg opplevde en teknisk feil. Vennligst prøv igjen eller kontakt kundeservice.",
                "category": "error",
                "needs_human": True,
                "steps": None,
                "sources": []
            }

    def _update_session_history(self, session_id: str, user_input: str, response: str):
        """Oppdater samtalehistorikk for en sesjon"""
        session_history = self.get_session_history(session_id)
        session_history.append(HumanMessage(content=user_input))
        session_history.append(AIMessage(content=response))

        # Behold bare de siste 10 meldingene for å unngå for lang kontekst
        if len(session_history) > 11:  # 1 system message + 10 dialog messages
            session_history = [session_history[0]] + session_history[-10:]

        self.active_sessions[session_id] = session_history

    def identify_problem_category(self, user_input: str) -> str:
        """Identifiser problemkategori basert på brukerens henvendelse"""
        categories = {
            "signal": ["signal", "bilde", "skjerm", "svart", "snø", "støy"],
            "decoder": ["dekoder", "boks", "fjernkontroll", "slår ikke på"],
            "channels": ["kanal", "program", "pakke", "mangler"]
        }
        
        for category, keywords in categories.items():
            if any(keyword in user_input.lower() for keyword in keywords):
                return category
        return "general"

    def _should_escalate(self, user_input: str, response: str) -> bool:
        """Vurder om henvendelsen bør eskaleres til menneskelig kundeservice"""
        complex_keywords = [
            "fungerer ikke i det hele tatt",
            "helt død",
            "krise",
            "akutt",
            "prøvd alt",
            "ingenting fungerer",
            "fortsatt ikke",
            "samme problem"
        ]
        return any(keyword in user_input.lower() for keyword in complex_keywords)

    def _get_troubleshooting_steps(self, category: str) -> Optional[List[str]]:
        """Hent feilsøkingstrinn for en gitt kategori"""
        try:
            if category in self.troubleshooting_data:
                for issue in self.troubleshooting_data[category]["common_issues"]:
                    return [step["description"] for step in issue["solutions"]]
        except Exception:
            pass
        return None
