from fastapi import FastAPI
import uvicorn
import logging

# Sett opp logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.get("/")
async def root():
    logger.info("Test-endepunkt kalt")
    return {"message": "Test server er aktiv"}

if __name__ == "__main__":
    logger.info("Starter test-server...")
    uvicorn.run(app, host="127.0.0.1", port=8080) 