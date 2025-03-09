import json
import os
from typing import Dict, List, Optional
from pathlib import Path

class RiksTVAgent:
    def __init__(self, index_path: str = None):
        """Initialiserer agenten med indeksfilen."""
        if index_path is None:
            # Standardplassering for indeksfilen
            index_path = r"C:\Users\Serve\OneDrive\Desktop\MIN KODEBASE\WEb scraber\RiksTV_Kundeservice\directory_index.json"
        
        with open(index_path, 'r', encoding='utf-8') as f:
            self.index = json.load(f)
        self.base_path = self.index['root_directory']
    
    def get_statistics(self) -> Dict:
        """Henter statistikk om dokumentasjonen."""
        return self.index['statistics']
    
    def search_documents(self, query: str, max_results: int = None) -> List[Dict]:
        """
        Søker etter dokumenter basert på nøkkelord.
        
        Args:
            query: Søkeord
            max_results: Maksimalt antall resultater (None = alle)
        """
        results = []
        for category in ['text', 'pdf', 'json']:
            for doc in self.index['files'][category]:
                if query.lower() in doc['name'].lower():
                    results.append({
                        'title': doc['name'].replace('-', ' ').replace('_', ' '),
                        'path': doc['path'],
                        'size': doc['size'],
                        'type': category,
                        'last_modified': doc.get('last_modified', 'Ukjent')
                    })
        
        results.sort(key=lambda x: x['size'], reverse=True)
        return results[:max_results] if max_results else results
    
    def get_document_content(self, path: str) -> Optional[str]:
        """Henter innholdet av et dokument."""
        full_path = os.path.join(self.base_path, path)
        if os.path.exists(full_path) and full_path.endswith('.txt'):
            with open(full_path, 'r', encoding='utf-8') as f:
                return f.read()
        return None
    
    def get_category_documents(self, category: str) -> List[Dict]:
        """Henter alle dokumenter i en bestemt kategori."""
        return self.index['files'].get(category, [])
    
    def find_related_documents(self, topic: str, max_results: int = None) -> List[Dict]:
        """
        Finner relaterte dokumenter basert på et tema.
        
        Args:
            topic: Tema å søke etter
            max_results: Maksimalt antall resultater (None = alle)
        """
        results = []
        for category in ['text', 'pdf', 'json']:
            for doc in self.index['files'][category]:
                path_parts = doc['path'].split('_')
                if any(topic.lower() in part.lower() for part in path_parts):
                    results.append({
                        'title': doc['name'].replace('-', ' ').replace('_', ' '),
                        'path': doc['path'],
                        'size': doc['size'],
                        'type': category,
                        'relevance': sum(1 for part in path_parts if topic.lower() in part.lower())
                    })
        
        # Sorter etter relevans
        results.sort(key=lambda x: x['relevance'], reverse=True)
        return results[:max_results] if max_results else results
    
    def get_topic_summary(self, topic: str) -> Dict:
        """
        Lager en oppsummering av et tema basert på alle relaterte dokumenter.
        
        Args:
            topic: Tema å oppsummere
        """
        related_docs = self.find_related_documents(topic)
        total_size = sum(doc['size'] for doc in related_docs)
        
        return {
            'topic': topic,
            'total_documents': len(related_docs),
            'total_size_bytes': total_size,
            'categories': {
                'text': len([doc for doc in related_docs if doc['type'] == 'text']),
                'pdf': len([doc for doc in related_docs if doc['type'] == 'pdf']),
                'json': len([doc for doc in related_docs if doc['type'] == 'json'])
            },
            'most_relevant_docs': [doc['title'] for doc in related_docs[:5]]
        }

    def get_answer_context(self, question: str, max_docs: int = 3) -> List[Dict]:
        """
        Finner relevante dokumenter som kan hjelpe med å svare på et spørsmål.
        Spesielt nyttig for Cursor AI.
        
        Args:
            question: Spørsmålet som skal besvares
            max_docs: Maksimalt antall dokumenter å returnere
        """
        # Del spørsmålet inn i nøkkelord
        keywords = question.lower().split()
        results = []
        
        for category in ['text', 'pdf', 'json']:
            for doc in self.index['files'][category]:
                score = 0
                doc_text = doc['name'].lower()
                
                # Beregn relevans score
                for keyword in keywords:
                    if keyword in doc_text:
                        score += 1
                
                if score > 0:
                    content = self.get_document_content(doc['path']) if doc['type'] == 'text' else None
                    results.append({
                        'title': doc['name'].replace('-', ' ').replace('_', ' '),
                        'path': doc['path'],
                        'content': content,
                        'score': score,
                        'type': doc['type']
                    })
        
        # Sorter etter relevans score
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:max_docs]

def main():
    """Hovedfunksjon for å demonstrere bruk av agenten."""
    agent = RiksTVAgent()
    
    # Test spørsmål-kontekst funksjonalitet
    question = "Hvordan fikser jeg problemer med strømmeboksen min?"
    print(f"\nSøker etter svar på: {question}")
    
    context = agent.get_answer_context(question)
    print("\nRelevante dokumenter funnet:")
    for doc in context:
        print(f"\nDokument: {doc['title']}")
        print(f"Type: {doc['type']}")
        print(f"Relevans score: {doc['score']}")
        if doc['content']:
            print("Utdrag fra innhold:")
            content = doc['content']
            print(content[:200] + "..." if len(content) > 200 else content)

if __name__ == "__main__":
    main() 