# Demo-Leitfaden

## Vorbereitung

Linux/macOS:

```bash
cd MultiAgentenMCP
./start-orderflow.sh
```

Windows: `start-windows.cmd` doppelt anklicken. Beim ersten Start werden Basisanwendung und MetaGPT
automatisch eingerichtet. Alternativ startet `docker compose up --build` die Basisanwendung auf
allen unterstützten Plattformen.

## Empfohlene Vorführung in sieben Minuten

1. **Problem erklären:** Eine Auftragsbestätigung benötigt Informationen aus mehreren betrieblichen
   Systemen. Manuelle Medienbrüche machen den Prozess langsam und fehleranfällig.
2. **Architektur zeigen:** Die Weboberfläche startet einen orchestrierten Prozess. Rollen rufen
   Unternehmensfunktionen ausschließlich über MCP-Werkzeuge auf.
3. **Animation erklären:** Den Präsentationsmodus aktivieren und die Prozesskette von Auftrag über
   MCP und MetaGPT bis zum Ergebnis verfolgen.
4. **Normalfall ausführen:** Bonität und Bestand reichen aus; der Auftrag kann bestätigt werden.
5. **Produktionsfall ausführen:** Im Tab „So wurde gerechnet“ Fehlmenge, Rüstzeit,
   Tageskapazität und Produktionsdauer erklären.
6. **Beschaffungsfall ausführen:** Bestand und interne Kapazität reichen nicht; ein Lieferant wird
   geprüft und der Termin neu berechnet.
7. **Ausnahme zeigen:** Beim gesperrten Kunden erzwingt das System eine manuelle Prüfung.
8. **Transparenz zeigen:** In den Tabs MCP-Daten und Prozessprotokoll lassen sich Datenquelle,
   Werkzeugaufruf und Entscheidung nachvollziehen.
9. **Erweiterbarkeit zeigen:** Den Stammdaten-Dialog öffnen und die kompakte Kunden- und
   Produktverwaltung demonstrieren.
10. **Dialogverwaltung zeigen:** Einen Kunden oder ein Produkt bearbeiten. Beim Löschen auf die
    zusätzliche Sicherheitsbestätigung und das gemeinsame Entfernen abhängiger Daten hinweisen.

## Kernaussage

Der Prototyp zeigt nicht, dass ein Sprachmodell autonom einen Auftrag freigeben sollte. Er zeigt,
wie ein Multi-Agentensystem einen BPM-Workflow koordinieren kann, während MCP den kontrollierten
Zugriff auf betriebliche Funktionen standardisiert. Kritische Fakten und Entscheidungen bleiben
regelbasiert und prüfbar.

## Falls MetaGPT nicht konfiguriert ist

Die Checkbox „Erklärung durch MetaGPT aktivieren“ deaktiviert lassen. Alle fachlichen Prozessschritte,
MCP-Aufrufe und Entscheidungen funktionieren weiterhin. Das ist ein gewollter Fallback und kein
Fehler der Demo.
