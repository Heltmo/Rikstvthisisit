from typing import Dict, List
import logging
from pydantic import BaseModel

class SignalIssue(BaseModel):
    description: str
    severity: str
    weather_related: bool
    steps: List[str]

class SignalService:
    def __init__(self):
        self.common_issues = {
            "no_signal": SignalIssue(
                description="Ingen signal på TV-en",
                severity="high",
                weather_related=False,
                steps=[
                    "Sjekk at alle kabler er koblet riktig til dekoderen",
                    "Kontroller at antennen er riktig tilkoblet",
                    "Prøv å restarte dekoderen ved å dra ut strømkabelen i 30 sekunder",
                    "Kjør kanalsøk på dekoderen"
                ]
            ),
            "poor_signal": SignalIssue(
                description="Dårlig eller ustabilt signal",
                severity="medium",
                weather_related=True,
                steps=[
                    "Sjekk værforhold i området",
                    "Kontroller antennens posisjon",
                    "Undersøk om det er fysiske hindringer foran antennen",
                    "Verifiser at antennekabelen ikke er skadet"
                ]
            ),
            "pixelation": SignalIssue(
                description="Pikselering eller frysing av bilde",
                severity="medium",
                weather_related=True,
                steps=[
                    "Sjekk signalstyrke i dekodermeny",
                    "Kontroller at antennekabelen er skikkelig festet",
                    "Prøv å optimalisere antennens posisjon",
                    "Vurder om det trengs en signalforsterker"
                ]
            )
        }
    
    async def diagnose_signal_issue(self, symptoms: str) -> Dict:
        """Diagnostiser signalproblemet basert på beskrevne symptomer"""
        try:
            if "ingen signal" in symptoms.lower():
                return self._create_response(self.common_issues["no_signal"])
            elif "hakking" in symptoms.lower() or "fryser" in symptoms.lower():
                return self._create_response(self.common_issues["pixelation"])
            elif "dårlig" in symptoms.lower() or "ustabilt" in symptoms.lower():
                return self._create_response(self.common_issues["poor_signal"])
            else:
                return {
                    "status": "unclear",
                    "message": "Kan du beskrive signalproblemet mer detaljert? "
                             "For eksempel: Ser du helt svart skjerm, eller er bildet hakkete?",
                    "steps": []
                }
        except Exception as e:
            logging.error(f"Feil ved diagnostisering av signalproblem: {str(e)}")
            return {
                "status": "error",
                "message": "Beklager, jeg kunne ikke diagnostisere problemet. "
                          "Vennligst kontakt kundeservice for assistanse.",
                "steps": []
            }
    
    def _create_response(self, issue: SignalIssue) -> Dict:
        """Opprett et strukturert svar basert på identifisert problem"""
        response = {
            "status": "diagnosed",
            "message": f"Jeg har identifisert problemet som: {issue.description}",
            "steps": issue.steps,
            "severity": issue.severity
        }
        
        if issue.weather_related:
            response["message"] += "\nMerk: Dette problemet kan være påvirket av værforhold."
            
        return response
    
    def get_signal_strength_guide(self) -> List[str]:
        """Returner guide for hvordan man sjekker signalstyrke"""
        return [
            "1. Trykk 'Meny' på RiksTV-fjernkontrollen",
            "2. Velg 'Innstillinger'",
            "3. Velg 'Installasjon' eller 'System'",
            "4. Finn 'Signalstyrke' eller 'Signalkvalitet'",
            "5. En signalstyrke på over 60% er normalt god"
        ] 