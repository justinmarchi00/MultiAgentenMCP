# Demo-Leitfaden

## Vorbereitung

```bash
cd /Users/justin/GitHub-Repo/MultiAgentenMCP
make setup
make check
make run
```

## Empfohlene Vorführung in fünf Minuten

1. **Problem erklären:** Eine Auftragsbestätigung benötigt Informationen aus mehreren betrieblichen
   Systemen. Manuelle Medienbrüche machen den Prozess langsam und fehleranfällig.
2. **Architektur zeigen:** Die Weboberfläche startet einen orchestrierten Workflow. Agenten rufen
   Unternehmensfunktionen ausschließlich über MCP-Werkzeuge auf.
3. **Normalfall ausführen:** Bonität und Bestand reichen aus; der Auftrag kann bestätigt werden.
4. **Beschaffungsfall ausführen:** Bestand und interne Kapazität reichen nicht; ein Lieferant wird
   geprüft und der Termin neu berechnet.
5. **Ausnahme zeigen:** Beim gesperrten Kunden erzwingt das System eine manuelle Prüfung.
6. **Transparenz zeigen:** In den Tabs MCP-Ergebnisse und Agentenprotokoll lassen sich Datenquelle,
   Werkzeugaufruf und Entscheidung nachvollziehen.

## Kernaussage

Der Prototyp zeigt nicht, dass ein Sprachmodell autonom einen Auftrag freigeben sollte. Er zeigt,
wie ein Multi-Agentensystem einen BPM-Workflow koordinieren kann, während MCP den kontrollierten
Zugriff auf betriebliche Funktionen standardisiert. Kritische Fakten und Entscheidungen bleiben
regelbasiert und prüfbar.

## Falls MetaGPT nicht konfiguriert ist

Die Checkbox „MetaGPT-Review verwenden“ deaktiviert lassen. Alle fachlichen Prozessschritte,
MCP-Aufrufe und Entscheidungen funktionieren weiterhin. Das ist ein gewollter Fallback und kein
Fehler der Demo.
