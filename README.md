# RiksTV AI Kundeservice

En AI-drevet chatbot for RiksTV kundeservice som hjelper kunder med vanlige problemer og spørsmål.

## Funksjoner

- 🤖 AI-drevet kundeservice-assistent
- 💬 Naturlig språkforståelse
- 📝 Husker samtalehistorikk
- 🔍 Intelligent problemløsning
- ⚡ Rask responstid
- 🎯 Presis kategorisering av henvendelser

## Teknologier

- FastAPI
- LangChain
- OpenAI
- Python 3.9+
- HTML/CSS/JavaScript

## Installasjon

1. Klon repositoriet:
```bash
git clone https://github.com/ditt-brukernavn/rikstv-ai-kundeservice.git
cd rikstv-ai-kundeservice
```

2. Opprett virtuelt miljø:
```bash
python -m venv venv
```

3. Aktiver virtuelt miljø:
```bash
# Windows
.\venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

4. Installer avhengigheter:
```bash
pip install -r requirements.txt
```

5. Opprett .env fil og legg til OpenAI API-nøkkel:
```bash
OPENAI_API_KEY=din-api-nøkkel-her
```

## Kjøring

Start serveren:
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8080
```

Åpne nettleseren og gå til:
```
http://127.0.0.1:8080
```

## Bruk

1. Skriv inn ditt spørsmål i chat-vinduet
2. Chatboten vil svare med relevant informasjon
3. Følg eventuelle trinnvise instruksjoner
4. Ved komplekse problemer vil du bli henvist til menneskelig kundeservice

## Bidrag

Ønsker du å bidra? Flott! 

1. Fork prosjektet
2. Opprett en feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit endringene dine (`git commit -m 'Add some AmazingFeature'`)
4. Push til branchen (`git push origin feature/AmazingFeature`)
5. Åpne en Pull Request

## Lisens

Dette prosjektet er lisensiert under MIT-lisensen - se [LICENSE](LICENSE) filen for detaljer.

## API-endepunkter

- `GET /`: Sjekk om tjenesten er oppe
- `