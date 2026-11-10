# Evaluationskonzept

## Fragestellung

Die Evaluation untersucht, ob der Prototyp unterschiedliche Prozesssituationen korrekt erkennt,
nachvollziehbar bearbeitet und ohne ein Sprachmodell reproduzierbare Ergebnisse liefert.

## Testfälle

| ID | Fall | Erwartung | Nachweis |
|---|---|---|---|
| T1 | Kunde freigegeben, Bestand ausreichend | Auftrag bestätigt | automatisierter Workflowtest |
| T2 | Bestand zu klein, Kapazität ausreichend | Produktion erforderlich | automatisierter Workflowtest |
| T3 | Bestand und Kapazität zu klein | Beschaffung wird geprüft | automatisierter Workflowtest |
| T4 | Kunde gesperrt | manuelle Prüfung | automatisierter Workflowtest |
| T5 | Produkt unbekannt | kontrollierter Fehlerfall | automatisierter Workflowtest |
| T6 | Menge null | Eingabe wird abgelehnt | Pydantic-Validierungstest |
| T7 | MCP-Werkzeuge | strukturierte Ergebnisse | MCP-Integrationstests |

## Bewertungskriterien

- **Funktionalität:** Werden die definierten Prozesspfade korrekt ausgeführt?
- **Nachvollziehbarkeit:** Sind Agent, Aktion, Datenquelle und Ergebnis im Protokoll erkennbar?
- **Reproduzierbarkeit:** Entsteht bei identischen Eingaben dieselbe Kernentscheidung?
- **Fehlerrobustheit:** Werden fehlende oder gesperrte Daten kontrolliert behandelt?
- **Erweiterbarkeit:** Lassen sich Werkzeuge oder reale Adapter ergänzen, ohne die UI umzubauen?

## Grenzen der Evaluation

Die Testdaten sind klein und synthetisch. Es werden weder reale Schnittstellen noch Lastverhalten,
Datenschutz, IT-Sicherheit oder wirtschaftliche Effekte im Produktivbetrieb gemessen. Aussagen zur
Zeit- oder Kostenersparnis sind deshalb nur als erwartetes Potenzial und nicht als empirisch
bestätigtes Ergebnis zu formulieren.
