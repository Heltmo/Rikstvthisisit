from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello from RiksTV AI Chatbot"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}
