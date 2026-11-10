# Zuordnung zur wissenschaftlichen Ausarbeitung

Die folgende Struktur hält den IT-bezogenen Teil kompakt und eignet sich für eine insgesamt auf
15 Seiten begrenzte Ausarbeitung.

## 4 Analyse der Multi-Agentenplattform und IT-Konzept

### 4.1 Architektur von MetaGPT

Rollen, Actions, Nachrichten und LLM-Anbindung beschreiben. Danach erklären, welche Teile im
Prototyp tatsächlich verwendet werden und welche bewusst regelbasiert bleiben.

### 4.2 Agentenmodell und Koordination

Auftrags-, Planungs-, Beschaffungs- und Validierungs-Agent sowie den zentralen Orchestrator
vorstellen. Das Ereignisprotokoll oder die Architekturabbildung als Nachweis verwenden.

### 4.3 Werkzeuge, Schnittstellen und MCP-Integration

MCP ausschreiben und als Protokoll zur standardisierten Bereitstellung von Kontext, Ressourcen und
Werkzeugen erklären. Die sechs implementierten Tools und die simulierten Zielsysteme tabellarisch
darstellen.

### 4.4 Integrationskonzept

JSON-Dateien als Stellvertreter für CRM, ERP, Lager, PPS und Einkauf einordnen. Anschließend die
mögliche Ablösung durch reale Adapter sowie Sicherheitsanforderungen diskutieren.

## 5 Prototypische Implementierung und Evaluation

### 5.1 Technische Umsetzung

Python 3.11, Streamlit, MetaGPT, MCP, Pydantic und Pytest nennen. Den Datenfluss vom Formular bis
zur validierten Entscheidung erklären.

### 5.2 Demonstration

Normalfall, Produktionsfall, Beschaffungsfall und gesperrten Kunden zeigen. Screenshots aus der
Weboberfläche mit kurzen Bildunterschriften verwenden.

### 5.3 Evaluation

Die Tests aus `docs/evaluation.md` zusammenfassen. Funktionalität, Nachvollziehbarkeit,
Reproduzierbarkeit und Grenzen bewerten.

### 5.4 Kritische Würdigung

Kleine synthetische Datenbasis, fehlende Produktivschnittstellen, LLM-Kosten und -Risiken sowie
fehlende produktive Sicherheitsmechanismen offen benennen. Als Vorteil die klare Trennung zwischen
deterministischer Entscheidung und optionaler KI-Erklärung herausstellen.
