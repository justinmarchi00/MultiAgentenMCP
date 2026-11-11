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
5. **Produktionsfall ausführen:** Im Tab „Berechnung“ Fehlmenge, Rüstzeit,
   Tageskapazität und Produktionsdauer erklären.
6. **Beschaffungsfall ausführen:** Produktion und Lieferant werden beide geprüft. Der schnellste
   Weg, der die gesamte Fehlmenge abdeckt, wird ausgewählt und der Termin neu berechnet.
7. **Ausnahme zeigen:** Bei einem gesperrten oder noch in Prüfung befindlichen Kunden erzwingt das
   System eine manuelle Prüfung. Das Szenario erscheint, sobald ein solcher Kunde vorhanden ist.
8. **Transparenz zeigen:** In den Tabs MCP-Daten und Prozessprotokoll lassen sich Datenquelle,
   Werkzeugaufruf und Entscheidung nachvollziehen.
9. **Erweiterbarkeit zeigen:** Den Stammdaten-Dialog öffnen und die kompakte Kunden- und
   Produktverwaltung demonstrieren.
10. **Dialogverwaltung zeigen:** „Neu anlegen“ oberhalb der Tabelle und die Bearbeiten-/Löschen-
    Aktionen rechts in den Zeilen verwenden. Beim Löschen auf die Sicherheitsbestätigung und das
    gemeinsame Entfernen abhängiger Produkt-, Kapazitäts- und Lieferantendaten hinweisen.

## Kernaussage

Der Prototyp zeigt nicht, dass ein Sprachmodell autonom einen Auftrag freigeben sollte. Er zeigt,
wie ein Multi-Agentensystem einen BPM-Workflow koordinieren kann, während MCP den kontrollierten
Zugriff auf betriebliche Funktionen standardisiert. Kritische Fakten und Entscheidungen bleiben
regelbasiert und prüfbar.

## Falls MetaGPT nicht konfiguriert ist

Die Checkbox „MetaGPT-Erklärung erstellen“ deaktiviert lassen. Alle fachlichen Prozessschritte,
MCP-Aufrufe und Entscheidungen funktionieren weiterhin. Das ist ein gewollter Fallback und kein
Fehler der Demo.
