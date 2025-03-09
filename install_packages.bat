@echo off
echo Installing packages...

pip install langchain==0.1.0
pip install openai==1.12.0
pip install python-dotenv==1.0.0
pip install fastapi==0.109.0
pip install uvicorn==0.27.0
pip install pydantic==2.5.3
pip install chromadb==0.4.22
pip install tiktoken==0.5.2
pip install python-multipart==0.0.6
pip install pypdf2==3.0.1
pip install unstructured==0.10.30
pip install pdf2image==1.16.3
pip install pytesseract==0.3.10

echo Installation complete!
pause 