# Architektur und Integrationskonzept

## Zielbild

Der Prototyp automatisiert einen vereinfachten Auftragsabwicklungsprozess. Er trennt dabei drei
Ebenen: Benutzeroberfläche und Prozesssteuerung, Agentenkoordination sowie Systemintegration. Die
Trennung macht sichtbar, welche Komponente eine Entscheidung vorbereitet und aus welcher Quelle
die verwendeten Daten stammen.

## Komponenten

1. **Streamlit-Weboberfläche:** nimmt den Auftrag an, verwaltet Demo-Stammdaten und visualisiert
   Prozess, Berechnungen sowie Ergebnisse.
2. **Prozess-Orchestrator:** steuert Reihenfolge, Fehlerbehandlung und Ergebniszusammenführung.
3. **Fachagenten:** bearbeiten klar abgegrenzte Rollen für Auftrag, Planung, Beschaffung und
   Validierung.
4. **MCP-Client:** ruft Werkzeuge mit strukturierten Parametern auf und liest strukturierte
   Ergebnisse ein.
5. **MCP-Server:** stellt Unternehmensfunktionen als standardisierte Werkzeuge bereit.
6. **Datenquellen:** JSON-Dateien simulieren CRM, Lager, PPS, Einkauf und ERP.
7. **MetaGPT-Erklärung:** optionaler, sprachmodellgestützter Erklärungs- und Validierungsschritt
   mit den Rollen Anna, Paul und Vera.

## Ablauf des Anwendungsfalls

| Prozessschritt | Zuständige Komponente | Ergebnis |
|---|---|---|
| Auftrag erfassen | Weboberfläche | strukturierter `OrderRequest` |
| Auftrag prüfen | Auftrags-Agent | formal gültige Pflichtdaten |
| Bonität prüfen | Planungs-Agent + MCP | Kundenstatus |
| Bestand prüfen | Planungs-Agent + MCP | Verfügbarkeit und Fehlmenge |
| Produktion planen | Planungs-Agent + MCP | Kapazität und Produktionsdauer |
| Beschaffung prüfen | Beschaffungs-Agent + MCP | Lieferant und Beschaffungszeit |
| Kalkulation | Planungs-Agent + MCP | Preis und Rabatt |
| Liefertermin bestimmen | Planungs-Agent + MCP | zugesagter Termin |
| Entscheidung validieren | Validierungs-Agent | Bestätigung oder manuelle Prüfung |

## Berechnung der Produktionsdauer

Die Produktionsdauer wird nicht von MetaGPT geschätzt. Das MCP-Werkzeug `check_capacity`
verwendet Produktstammdaten aus der simulierten Produktionsplanung:

1. `Tageskapazität = Wochenkapazität / Arbeitstage pro Woche`
2. `Bearbeitungstage = aufrunden(Fehlmenge / Tageskapazität)`
3. `Produktionsdauer = Rüst- und Planungstage + Bearbeitungstage`

`calculate_delivery_date` addiert diese Dauer als Arbeitstage zum Planungsdatum und überspringt
Samstag und Sonntag. Der zugesagte Termin ist das spätere Datum aus Kundenwunsch und frühestem
realisierbaren Termin.

Vor der Terminberechnung wählt der Orchestrator genau einen vollständigen Erfüllungsweg:
Lagerbestand, Produktion innerhalb einer Woche, vollständige externe Beschaffung oder
mehrwöchige interne Produktion. Reicht keiner dieser Wege für die gesamte Fehlmenge aus, wird
kein scheinbar genauer Liefertermin ausgegeben, sondern eine manuelle Planung verlangt.

## Koordination und Kooperation

Der Orchestrator koordiniert die Reihenfolge. Agenten kooperieren indirekt über einen gemeinsamen,
strukturierten Workflowzustand. Ergebnisse werden nicht als unkontrollierter Freitext, sondern als
typisierte Daten weitergereicht. Das optionale MetaGPT-Team erhält erst nach Abschluss der
MCP-Abfragen einen unveränderlichen Faktenblock. Seine Aufgabe ist die Erklärung, nicht die
Festlegung betrieblicher Werte.

Die Bezeichnungen in der Oberfläche und in den sichtbaren Ergebnisstrukturen sind deutsch.
Technische Python-Bezeichner und MCP-Werkzeugnamen bleiben aus Gründen der Wartbarkeit und
Interoperabilität englisch; sie werden für die Demonstration in verständliche deutsche Namen
übersetzt.

## Integrationsprinzip

MCP bildet die Integrationsschicht. Der Client kennt nur Werkzeugnamen, Eingabeparameter und
Rückgabestrukturen. Die konkrete Datenquelle bleibt hinter dem Server verborgen. Daher könnten die
JSON-Zugriffe später durch SAP-, CRM-, Datenbank- oder REST-Adapter ersetzt werden, ohne den
gesamten Workflow neu zu entwerfen.

## Sicherheits- und Qualitätsentscheidungen

- Validierung der Eingaben durch Pydantic
- keine Geheimnisse im Repository
- keine schreibenden Zugriffe auf reale Systeme
- deterministische Kernentscheidung statt LLM-Entscheidung
- nachvollziehbares Ereignisprotokoll
- klarer Fallback, wenn MetaGPT oder ein LLM nicht verfügbar ist
- automatisierte Tests für Normal- und Ausnahmefälle

Für einen produktiven Betrieb fehlen insbesondere Authentifizierung, Autorisierung,
Mandantentrennung, Datenschutzkonzept, Monitoring, Transaktionen, Wiederholungslogik und eine
verbindliche menschliche Freigabe für risikoreiche Entscheidungen.
