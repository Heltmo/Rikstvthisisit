from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from enum import Enum
from .core.agent import RiksTVAgent
import logging
import os

# Sett opp logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Category(str, Enum):
    SIGNAL = "signal"
    DECODER = "decoder"
    GENERAL = "general"

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
rikstv_agent = RiksTVAgent()

# Lagre aktive sesjoner
active_sessions: Dict[str, RiksTVAgent] = {}

@app.get("/")
async def root():
    return FileResponse("app/static/index.html")

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        logger.info(f"Mottok chat-forespørsel: {request.message[:50]}...")
        
        # Håndter sesjoner
        session_id = request.session_id or "default"
        if session_id not in active_sessions:
            logger.info(f"Oppretter ny sesjon: {session_id}")
            active_sessions[session_id] = RiksTVAgent()
        
        agent = active_sessions[session_id]
        
        # Håndter henvendelsen med AI-agenten
        logger.info("Sender forespørsel til AI-agent")
        response = await agent.handle_query(request.message, session_id)
        
        logger.info("Behandler respons fra AI-agent")
        return ChatResponse(
            response=response["response"],
            category=response["category"],
            needs_human=response["needs_human"],
            steps=response.get("steps")
        )
            
    except Exception as e:
        logger.error(f"Feil i chat-endepunkt: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    logger.info("Helsejekk utført")
    return {
        "status": "healthy",
        "version": "1.0.0",
        "active_sessions": len(active_sessions)
    }

if __name__ == "__main__":
    import uvicorn
    logger.info("Starter server på port 8080...")
    uvicorn.run(app, host="127.0.0.1", port=8080) 