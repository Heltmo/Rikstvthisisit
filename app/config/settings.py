from pydantic import BaseModel
from typing import Dict
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseModel):
    # API-nøkler og autentisering
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # LLM-konfigurasjon
    MODEL_NAME: str = os.getenv("MODEL_NAME", "gpt-3.5-turbo")
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.7"))
    MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "500"))
    
    # Vektordatabase-innstillinger
    VECTOR_DB_PATH: str = "knowledge/vector_db"
    
    # Kundeservice-innstillinger
    MAX_RETRIES: int = 3
    ESCALATION_THRESHOLD: float = 0.8
    
    # Predefinerte meldinger
    GREETING_MESSAGE: str = "Hei! Jeg er RiksTVs digitale kundeserviceassistent. Hvordan kan jeg hjelpe deg i dag?"
    ESCALATION_MESSAGE: str = "Jeg beklager, men dette virker som et komplekst problem. La meg sette deg i kontakt med en av våre kundeservicemedarbeidere."
    
    # Feilsøkingskategorier
    TROUBLESHOOTING_CATEGORIES: Dict[str, str] = {
        "signal": "Signalproblemer",
        "decoder": "Dekoder og utstyr",
        "channels": "Kanalproblemer",
        "subscription": "Abonnement og betaling",
        "connection": "Tilkobling og internett"
    }

settings = Settings() 