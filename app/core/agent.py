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

class RiksTVAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            temperature=settings.TEMPERATURE,
            model_name=settings.MODEL_NAME,
            max_tokens=settings.MAX_TOKENS,
            api_key=settings.OPENAI_API_KEY
        )
        
        # Initialiser chat-historikk med system-melding
        self.system_prompt = """Du er en AI-kundeserviceassistent for RiksTV. Din oppgave er å hjelpe kunder med TV-tjenester, signalproblemer, dekodere, kanaler, abonnementer og tilkobling.

RETNINGSLINJER:
1. SVARFORMAT
   - Gi korte, presise svar når mulig
   - Bruk punktlister for trinnvise instruksjoner
   - Utvid svar kun når detaljert veiledning er nødvendig

2. SAMTALEFLYT
   - Behold kontekst fra tidligere meldinger
   - Still oppfølgingsspørsmål hvis noe er uklart
   - Bekreft løsninger når kunden rapporterer resultater

3. ESKALERING
   - Eskaler til menneskelig kundeservice ved:
     * Komplekse tekniske problemer
     * Ukjente feil
     * Gjentatte mislykkede løsningsforsøk
   - Bruk formuleringen: "Jeg forstår problemet ditt. La meg sette deg i kontakt med en av våre kundeservice-medarbeidere som kan hjelpe deg videre."

4. KUNNSKAPSOMRÅDER
   - Hold deg til disse temaene:
     * TV-signal og dekodere
     * Kanaler og programpakker
     * Abonnement og betaling
     * Tilkobling og internett
   - Si "beklager, dette er utenfor mitt kompetanseområde" for andre temaer

5. KOMMUNIKASJONSSTIL
   - Vær høflig og profesjonell
   - Bruk enkelt, forståelig språk
   - Vis empati ved problemer
   - Bekreft kundens frustrasjon når relevant

VIKTIG:
- Start alltid nye samtaler med: "Hei! Jeg er RiksTVs digitale assistent. Hvordan kan jeg hjelpe deg i dag?"
- Følg opp løsningsforslag med: "Hjalp dette deg å løse problemet?"
- Ved eskalering, forklar alltid hvorfor du eskalerer

EKSEMPLER PÅ GOD KOMMUNIKASJON:
Kunde: "TV-en viser bare svart skjerm"
Svar: "La oss løse dette sammen. Først, sjekk disse punktene:
1. Er dekoderen slått på? (sjekk at den lyser)
2. Er HDMI-kabelen koblet til både dekoder og TV?
3. Er riktig HDMI-inngang valgt på TV-en?

Hvilket punkt vil du at vi skal sjekke først?"

Kunde: "Har prøvd alt dette, ingenting fungerer"
Svar: "Jeg forstår at dette er frustrerende. Siden vi har prøvd de vanlige løsningene uten resultat, vil jeg sette deg i kontakt med en av våre kundeservice-medarbeidere som kan hjelpe deg videre med mer avansert feilsøking."

HUSK: Din hovedprioritet er å hjelpe kunden effektivt og profesjonelt."""

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
    
    def load_knowledge_base(self):
        """Last inn kunnskapsbasen fra JSON-filer og dokumenter"""
        try:
            with open("app/knowledge/data/troubleshooting.json", "r", encoding="utf-8") as f:
                self.troubleshooting_data = json.load(f)
            with open("app/knowledge/data/faq.json", "r", encoding="utf-8") as f:
                self.faq_data = json.load(f)
            
            # Prosesser dokumenter
            self.pdf_processor.process_all_documents()
            
        except Exception as e:
            logging.error(f"Kunne ikke laste kunnskapsbase: {str(e)}")
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
            category = self.identify_problem_category(user_input)
            
            # Hent samtalehistorikk for sesjonen
            session_history = self.get_session_history(session_id)
            
            # Søk i dokumenter etter relevant informasjon
            doc_results = await self.pdf_processor.search_documents(user_input)
            
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
            
            # Generer svar ved hjelp av LLM med samtalehistorikk
            response = self.chain.invoke({
                "chat_history": session_history,
                "input": full_input
            })
            
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
        for category, _ in settings.TROUBLESHOOTING_CATEGORIES.items():
            if category.lower() in user_input.lower():
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