from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from enum import Enum
from .core.agent import RiksTVAgent
import logging
import os
import traceback

# Sett opp logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Category(str, Enum):
    SIGNAL = "signal"
    DECODER = "decoder"
    GENERAL = "general"
    CHANNELS = "channels"  # Legg til denne linjen
    ERROR = "error"  # Legg til denne linjen

class ChatRequest(BaseModel):
    message: str = Field(...,
        description="Brukerens melding eller spørsmål",
        example="Jeg har problemer med TV-signalet")
    session_id: Optional[str] = Field(None,
        description="Valgfri session ID for å spore samtalen",
        example="test-123")

class ChatResponse(BaseModel):
    response: str = Field(...,
        description="AI-assistentens svar")
    category: Category = Field(default=Category.GENERAL,
        description="Kategorien for henvendelsen")
    needs_human: bool = Field(default=False,
        description="Indikerer om saken bør eskaleres til menneskelig kundeservice")
    steps: Optional[List[str]] = Field(None,
        description="Liste over feilsøkingstrinn hvis relevant")

app = FastAPI(
    title="RiksTV AI Kundeservice",
    description="AI-drevet kundeservicesystem for RiksTV",
    version="1.0.0"
)

# Opprett templates
templates = Jinja2Templates(directory="app/templates")

# CORS-konfigurasjon
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Opprett static-mappe hvis den ikke eksisterer
os.makedirs("app/static", exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Initialiser AI-agent
logger.info("Initialiserer RiksTV AI Agent...")
try:
    rikstv_agent = RiksTVAgent()
    logger.info("RiksTV AI Agent initialisert vellykket")
except Exception as e:
    logger.error(f"Feil ved initialisering av RiksTV AI Agent: {str(e)}")
    logger.error(traceback.format_exc())
    rikstv_agent = None

# Lagre aktive sesjoner
active_sessions: Dict[str, RiksTVAgent] = {}

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        logger.info(f"Mottok chat-forespørsel: {request.message[:50]}...")

        if rikstv_agent is None:
            logger.error("RiksTV AI Agent er ikke initialisert")
            return ChatResponse(
                response="Beklager, tjenesten er midlertidig utilgjengelig. Vennligst prøv igjen senere.",
                category=Category.GENERAL,
                needs_human=True,
                steps=None
            )

        # Håndter sesjoner
        session_id = request.session_id or "default"
        
        # Håndter henvendelsen med AI-agenten
        logger.info("Sender forespørsel til AI-agent")
        response = await rikstv_agent.handle_query(request.message, session_id)

        # Konverter kategori til gyldig enum-verdi
        category = response["category"]
        if category not in [c.value for c in Category]:
            category = Category.GENERAL.value

        logger.info("Behandler respons fra AI-agent")
        return ChatResponse(
            response=response["response"],
            category=category,
            needs_human=response["needs_human"],
            steps=response.get("steps")
        )

    except Exception as e:
        logger.error(f"Feil i chat-endepunkt: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chat", response_model=ChatResponse)
async def chat_get(message: str, session_id: Optional[str] = None):
    try:
        logger.info(f"Mottok GET chat-forespørsel: {message[:50]}...")

        if rikstv_agent is None:
            logger.error("RiksTV AI Agent er ikke initialisert")
            return ChatResponse(
                response="Beklager, tjenesten er midlertidig utilgjengelig. Vennligst prøv igjen senere.",
                category=Category.GENERAL,
                needs_human=True,
                steps=None
            )

        # Håndter sesjoner
        session_id = session_id or "default"
        
        # Håndter henvendelsen med AI-agenten
        logger.info("Sender forespørsel til AI-agent")
        response = await rikstv_agent.handle_query(message, session_id)

        # Konverter kategori til gyldig enum-verdi
        category = response["category"]
        if category not in [c.value for c in Category]:
            category = Category.GENERAL.value

        logger.info("Behandler respons fra AI-agent")
        return ChatResponse(
            response=response["response"],
            category=category,
            needs_human=response["needs_human"],
            steps=response.get("steps")
        )

    except Exception as e:
        logger.error(f"Feil i chat-endepunkt: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    logger.info("Helsejekk utført")
    return {
        "status": "healthy",
        "version": "1.0.0",
        "agent_status": "initialized" if rikstv_agent is not None else "failed"
    }

if __name__ == "__main__":
    import uvicorn
    logger.info("Starter server på port 8080...")
    uvicorn.run(app, host="127.0.0.1", port=8080)
