# Textgrundlage für den IT-bezogenen Teil der Ausarbeitung

Dieses Dokument enthält eine ausformulierte Grundlage für die Kapitel 4 und 5 der
wissenschaftlichen Ausarbeitung. Die Sprache ist bewusst verständlich gehalten. Vor der Abgabe
müssen die Nummerierung, Abbildungsverweise und das Literaturverzeichnis an das gemeinsame
Dokument der Projektgruppe angepasst werden.

## 4 Analyse der Multi-Agentenplattform und IT-Konzept

### 4.1 Architektur von MetaGPT

MetaGPT ist ein Open-Source-Framework für die Zusammenarbeit mehrerer sprachmodellgestützter
Agenten. Die Grundidee besteht darin, eine größere Aufgabe nicht durch einen einzigen allgemeinen
Agenten bearbeiten zu lassen. Stattdessen werden unterschiedliche Rollen mit eigenen Zielen,
Aufgaben und Regeln festgelegt. Die Entwickler von MetaGPT beschreiben dieses Vorgehen als eine
Art digitale Arbeitskette. Standardisierte Arbeitsabläufe, sogenannte Standard Operating
Procedures, legen fest, welche Rolle wann tätig wird und welches Ergebnis an die nächste Rolle
weitergegeben wird [1]. Dadurch soll die Zusammenarbeit strukturierter ablaufen als bei einer
freien Unterhaltung mehrerer Sprachmodelle.

Wichtige Bausteine des Frameworks sind `Role`, `Action`, `Message` und `Environment`. Eine Rolle
beschreibt, wer handelt, welches Ziel verfolgt wird und welche Einschränkungen gelten. Eine Action
legt die konkrete Tätigkeit einer Rolle fest, beispielsweise die Analyse eines Auftrags oder die
Prüfung eines Ergebnisses. Messages transportieren die Arbeitsergebnisse zwischen den Rollen. Das
Environment bildet den gemeinsamen Arbeitsraum, in dem Rollen Nachrichten beobachten und darauf
reagieren können. Im Quellcode von MetaGPT werden Actions einer Rolle über `set_actions()`
zugeordnet. Außerdem können unterschiedliche Reaktionsarten verwendet werden, zum Beispiel eine
feste Reihenfolge oder ein ReAct-Ablauf [2; 3].

Der Prototyp nutzt diese Möglichkeiten bewusst nur in einem abgegrenzten Teil des Prozesses. Die
betrieblichen Werte und die eigentliche Entscheidung werden regelbasiert berechnet. Erst danach
erhalten drei MetaGPT-Rollen einen kontrollierten Faktenblock. Anna beschreibt den Auftrag aus
kaufmännischer Sicht. Paul baut auf Annas Beitrag auf und erklärt die Planung. Vera erhält beide
Texte und prüft sie gegen die berechneten Fakten. MetaGPT dient damit als Erklärungs- und
Prüfschicht, nicht als Quelle für Bestände, Preise oder Liefertermine. Diese Trennung reduziert das
Risiko, dass erfundene Werte des Sprachmodells direkt in die Prozessentscheidung eingehen.

### 4.2 Agentenmodell, Koordination und Kooperation

Das Agentenmodell des Prototyps besteht aus zwei Ebenen. Auf der ersten Ebene stehen die logischen
Prozessrollen für Auftrag, Planung, Beschaffung, Kalkulation und Validierung. Sie werden vom
Prozess-Orchestrator in einer festgelegten Reihenfolge aufgerufen und im Ereignisprotokoll sichtbar
gemacht. Diese Rollen sind im aktuellen Prototyp keine eigenständigen MetaGPT-Objekte, sondern klar
getrennte Aufgaben innerhalb des Python-Workflows. Diese vereinfachte Umsetzung reicht aus, um die
fachliche Arbeitsteilung nachvollziehbar darzustellen.

Auf der zweiten Ebene befinden sich die tatsächlichen MetaGPT-Rollen Anna, Paul und Vera. Jede
Rolle besitzt ein eigenes Ziel, eigene Einschränkungen und genau eine Action. Ihre Zusammenarbeit
erfolgt nacheinander. Anna erhält zunächst die strukturierten Auftragsdaten. Paul erhält dieselben
Fakten und zusätzlich Annas Ergebnis. Vera bekommt schließlich die Fakten sowie beide vorherigen
Beiträge. Dadurch entsteht für jeden Auftrag eine gemeinsame Kontextkette. Sie verhindert, dass
die drei Rollen lediglich dreimal dieselbe Zusammenfassung erzeugen.

Die Koordination übernimmt der zentrale Orchestrator. Er prüft Pflichtdaten, startet die
MCP-Werkzeugaufrufe, sammelt die Ergebnisse und wählt den weiteren Prozessweg. Die Agenten
kooperieren dabei über einen strukturierten Workflowzustand. Geschäftsdaten werden nicht als
unkontrollierter Freitext weitergegeben, sondern in eindeutig benannten Feldern. Für jeden neuen
Auftrag werden die MetaGPT-Rollen neu erzeugt. Es gibt absichtlich kein auftragsübergreifendes
Gedächtnis, damit keine Daten eines vorherigen Kunden in einen neuen Vorgang gelangen.

### 4.3 Werkzeuge, Schnittstellen und MCP-Integration

MCP steht für Model Context Protocol. Es handelt sich um ein offenes Protokoll, mit dem
KI-Anwendungen auf standardisierte Weise Werkzeuge und Datenquellen ansprechen können. Die
offizielle Spezifikation unterscheidet zwischen Host, Client und Server. Der Host ist die
übergeordnete Anwendung, der Client stellt die Verbindung her und der Server bietet seine
Funktionen an. Die Kommunikation basiert auf strukturierten Nachrichten. In der aktuellen
Spezifikation werden dafür JSON-RPC-Nachrichten verwendet [4]. Ein Server kann unter anderem
Tools, Ressourcen und Prompt-Vorlagen bereitstellen. Im Prototyp werden ausschließlich Tools
benötigt.

Der MCP-Server stellt sechs Werkzeuge bereit:

| Werkzeug | Aufgabe | Simuliertes Unternehmenssystem |
|---|---|---|
| `get_customer` | Kundendaten und Bonität abrufen | CRM |
| `check_stock` | Bestand und Fehlmenge ermitteln | Lagerverwaltung |
| `check_capacity` | Produktionskapazität und Dauer berechnen | PPS/MES |
| `check_procurement` | Lieferant und Beschaffungsmöglichkeit prüfen | Einkauf/SRM |
| `calculate_price` | Preis und Mengenrabatt berechnen | ERP/Kalkulation |
| `calculate_delivery_date` | möglichen Liefertermin bestimmen | ERP/Disposition |

Der MCP-Client ruft diese Werkzeuge mit strukturierten Parametern auf und verarbeitet die
Rückgaben. Die Python-Bibliothek erzeugt aus den Typangaben der Funktionen die benötigten
Werkzeugbeschreibungen und Schemata. Dieses Vorgehen entspricht dem Grundprinzip des offiziellen
Python-SDKs [5]. Im normalen Ablauf verwendet der Prototyp eine direkte Verbindung zwischen
Client und Server innerhalb des Programms. Für Untersuchungen mit dem MCP Inspector kann der
Server separat gestartet werden. Zusätzlich ist ein Start über Streamable HTTP vorgesehen.

MCP ist hier deshalb mehr als nur eine beliebige Programmierschnittstelle. Der Workflow kennt nur
die Werkzeugnamen, Eingabeparameter und Rückgabestrukturen. Wie der Server intern an die Daten
gelangt, bleibt verborgen. Dadurch könnten die JSON-Dateien später durch Datenbankabfragen,
REST-Schnittstellen oder Adapter für betriebliche Systeme ersetzt werden, ohne die gesamte
Prozesssteuerung neu zu entwickeln.

### 4.4 Integrationskonzept und Systemlandschaft

Die Systemlandschaft wird im Prototyp durch lokale JSON-Dateien simuliert. Kundendaten stehen für
ein CRM-System. Produkt- und Preisdaten bilden einen kleinen Ausschnitt eines ERP-Systems ab.
Bestände repräsentieren die Lagerverwaltung, Kapazitätsdaten die Produktionsplanung und
Lieferantendaten den Einkauf. Der MCP-Server übernimmt die Rolle einer Integrationsschicht und
stellt diese unterschiedlichen Informationen in einheitlicher Form bereit.

Für eine reale Einführung müssten die lokalen Datenzugriffe durch abgesicherte Adapter ersetzt
werden. Denkbar wären beispielsweise REST-APIs, Datenbankzugriffe oder ein SAP-Adapter. Zusätzlich
wären Authentifizierung, Rollen und Rechte, verschlüsselte Verbindungen, Protokollierung,
Datenschutz, Transaktionen und eine menschliche Freigabe für kritische Entscheidungen notwendig.
Die MCP-Spezifikation weist ausdrücklich darauf hin, dass Datenzugriffe und Werkzeugaufrufe nur
mit geeigneter Kontrolle und Zustimmung erfolgen dürfen [4]. Der Prototyp zeigt daher ein
Integrationsprinzip, stellt aber noch keine produktionsreife Unternehmensintegration dar.

## 5 Prototypische Implementierung und Evaluation

### 5.1 Technische Umsetzung

Der Prototyp wurde mit Python 3.11 umgesetzt. Streamlit stellt die Weboberfläche bereit. Beim
lokalen Start läuft das Python-Backend als Server und die Benutzeroberfläche wird im Browser
angezeigt. Diese Client-Server-Struktur entspricht dem von Streamlit beschriebenen
Anwendungsmodell [6]. Pydantic validiert die Eingabedaten. Das offizielle MCP-Python-Paket bildet
Client, Server und Werkzeugaufrufe ab. Pytest wird für automatisierte Tests verwendet. MetaGPT
läuft wegen seiner eigenen Abhängigkeiten in einer getrennten virtuellen Python-Umgebung.

Der Benutzer wählt einen Kunden, ein Produkt, eine Menge und einen Wunschtermin aus. Anschließend
validiert der Orchestrator den Auftrag und ruft die benötigten MCP-Werkzeuge auf. Aus Bonität,
Bestand, Produktionskapazität, Beschaffungszeit, Preis und Termin wird eine reproduzierbare
Kernentscheidung abgeleitet. Falls MetaGPT aktiviert ist, erhalten Anna, Paul und Vera danach die
bereits kontrollierten Ergebnisse. Fällt MetaGPT aus oder fehlt ein API-Schlüssel, bleibt der
regelbasierte Geschäftsprozess trotzdem nutzbar.

Die Stammdatenverwaltung erlaubt das Anlegen, Bearbeiten und Löschen von Demo-Kunden und
Demo-Produkten. Änderungen werden lokal in JSON-Dateien gespeichert. Die Anwendung läuft nativ
unter Windows, Linux und macOS. Alternativ kann die Basisanwendung über Docker gestartet werden.

### 5.2 Demonstration des Prototyps

Für die Demonstration stehen vier grundlegende Situationen zur Verfügung. Im Normalfall sind
Bonität und Bestand ausreichend, sodass der Auftrag bestätigt werden kann. Im Produktionsfall
fehlt ein Teil der Menge, kann aber intern hergestellt werden. Im Beschaffungsfall deckt ein
Lieferant die vollständige Fehlmenge schneller ab als die Produktion. Ist die Bonität gesperrt
oder noch in Prüfung, wird keine automatische Freigabe erteilt.

Die Weboberfläche zeigt die einzelnen Prozessschritte, den zuständigen Agenten, die verwendeten
MCP-Werkzeuge und das Ergebnis. Im Berechnungsbereich lassen sich Bestands-, Preis- und
Terminberechnung nachvollziehen. Der MetaGPT-Bereich stellt die Beiträge von Anna, Paul und Vera
nebeneinander dar. Auf diese Weise wird sowohl der technische Datenfluss als auch die
Zusammenarbeit der Rollen sichtbar.

### 5.3 Evaluation

Die Evaluation prüft, ob die festgelegten Prozesspfade korrekt erkannt werden und bei gleichen
Eingaben dieselbe Kernentscheidung entsteht. Am 17. November 2026 wurden Linting und Tests mit
`make check` ausgeführt. Alle 32 automatisierten Tests wurden erfolgreich abgeschlossen. Die
gemessene Codeabdeckung lag insgesamt bei 69 Prozent.

Die Tests decken unter anderem den Normalfall, interne Produktion, externe Beschaffung,
Bonitätsprobleme, unbekannte Produkte und ungültige Mengen ab. Zusätzlich werden strukturierte
MCP-Rückgaben, die Produktionsdauer, Wochenenden bei der Terminberechnung, mehrwöchige Produktion,
unvollständige Lieferantenmengen und die Stammdatenverwaltung geprüft. Auch die Weitergabe des
Kontexts zwischen Anna, Paul und Vera sowie das Ausblenden eines API-Schlüssels in Fehlermeldungen
werden getestet.

Das Ergebnis zeigt, dass die regelbasierte Kernlogik für die definierten Testdaten reproduzierbar
arbeitet. Die automatisierte Testsuite führt jedoch keinen kostenpflichtigen Live-Aufruf des
Sprachmodells durch. Sie prüft den MetaGPT-Adapter, die Kontextbildung und die Fehlerbehandlung.
Die sprachliche Qualität der echten MetaGPT-Ausgaben muss deshalb ergänzend in der Vorführung oder
mit dokumentierten Beispielaufträgen bewertet werden. Auch Lastverhalten und die Anbindung realer
Unternehmenssysteme sind nicht Teil der Evaluation.

### 5.4 Kritische Würdigung

Eine Stärke des Prototyps ist die klare Trennung zwischen berechneten Geschäftsdaten und
sprachlicher KI-Erklärung. Bestände, Preise und Termine stammen aus nachvollziehbaren Werkzeugen.
Dadurch bleibt die Kernentscheidung auch ohne MetaGPT funktionsfähig. Das Ereignisprotokoll und die
Berechnungsansicht machen sichtbar, wie ein Ergebnis zustande kommt. MCP erleichtert außerdem eine
spätere Ablösung der simulierten Datenquellen.

Gleichzeitig ist die Aussagekraft begrenzt. Die Datenbasis ist klein und künstlich. Die logischen
Prozessrollen sind nur teilweise als echte MetaGPT-Agenten umgesetzt. Eine reale
Unternehmensintegration, ein vollständiges Berechtigungskonzept und eine Untersuchung unter hoher
Last fehlen. Sprachmodellausgaben können trotz klarer Prompts ungenau sein und verursachen Kosten.
Deshalb darf MetaGPT im aktuellen Konzept keine betrieblichen Werte verändern. Für einen
Produktivbetrieb wären zusätzliche Sicherheitsmaßnahmen, Monitoring und verbindliche menschliche
Freigaben erforderlich.

## Quellen für diesen Abschnitt

[1] Hong, S. et al. (2024): *MetaGPT: Meta Programming for a Multi-Agent Collaborative
Framework*. ICLR 2024. <https://doi.org/10.48550/arXiv.2308.00352>

[2] FoundationAgents (2026): *MetaGPT – The Multi-Agent Framework*. GitHub-Repository.
<https://github.com/FoundationAgents/MetaGPT>

[3] FoundationAgents (2026): *Role implementation in MetaGPT*. GitHub-Quellcode.
<https://github.com/FoundationAgents/MetaGPT/blob/main/metagpt/roles/role.py>

[4] Model Context Protocol (2026): *MCP Specification, Version 2026-07-28*.
<https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2026-07-28/index.mdx>

[5] Model Context Protocol (2026): *MCP Python SDK – First Steps*.
<https://py.sdk.modelcontextprotocol.io/get-started/first-steps/>

[6] Streamlit (2026): *Understanding Streamlit's client-server architecture*.
<https://docs.streamlit.io/develop/concepts/architecture/architecture>
