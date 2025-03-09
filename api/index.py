from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import os
import sys

# Legg til prosjektets rotmappe i sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importer app fra app.main
from app.main import app as fastapi_app

# Eksporter app for Vercel
app = fastapi_app
