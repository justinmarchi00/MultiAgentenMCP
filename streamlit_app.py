from __future__ import annotations

import asyncio
import re
from datetime import date, datetime, timedelta
from html import escape
from typing import Any

import streamlit as st
from dotenv import load_dotenv

from orderflow.data_store import (
    add_customer,
    add_product,
    delete_customer,
    delete_product,
    list_capacity,
    list_customers,
    list_products,
    list_suppliers,
    update_customer,
    update_product,
)
from orderflow.metagpt_agents import metagpt_available, metagpt_configured
from orderflow.models import EventLevel, OrderRequest, WorkflowDecision
from orderflow.workflow import run_order_workflow

load_dotenv()

st.set_page_config(
    page_title="OrderFlow AI",
    page_icon=":material/schema:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
      :root {
        --navy:#11213d;
        --blue:#2563eb;
        --blue-soft:#eff6ff;
        --teal:#0f9f91;
        --green:#12805c;
        --amber:#b66a08;
        --red:#c33d3d;
        --line:#dbe5f1;
        --muted:#64748b;
      }
      .stApp {
        background:
          radial-gradient(circle at 90% 0%, rgba(37,99,235,.07), transparent 28rem),
          #f6f8fc;
      }
      .block-container {
        max-width:none !important;
        padding:1rem 1.35rem 1.2rem !important;
      }
      header[data-testid="stHeader"] {display:none;}
      [data-testid="stToolbar"] {display:none;}
      [data-testid="stForm"] {
        border:1px solid var(--line);
        border-radius:18px;
        background:rgba(255,255,255,.88);
        box-shadow:0 8px 28px rgba(15,23,42,.045);
        padding:1rem;
      }
      [data-testid="stMetric"] {
        background:white;
        border:1px solid var(--line);
        border-radius:14px;
        padding:.65rem .8rem;
        box-shadow:0 6px 20px rgba(15,23,42,.04);
      }
      [data-testid="stMetricLabel"] {font-size:.76rem;}
      [data-testid="stMetricValue"] {font-size:1.12rem;color:var(--navy);}
      div[role="dialog"] {width:min(1120px,94vw) !important;max-width:1120px !important;}
      div[role="dialog"] [data-testid="stForm"] {box-shadow:none;}
      .of-svg {
        width:1.15rem;height:1.15rem;display:inline-block;vertical-align:-.2rem;
        fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;
        stroke-linejoin:round;
      }
      .of-header {
        display:flex;align-items:center;gap:.85rem;
        min-height:3.2rem;
      }
      .of-logo {
        width:2.75rem;height:2.75rem;border-radius:13px;display:grid;place-items:center;
        color:white;background:linear-gradient(135deg,#183d89,#2563eb 62%,#0f9f91);
        box-shadow:0 8px 22px rgba(37,99,235,.22);
      }
      .of-logo .of-svg {width:1.55rem;height:1.55rem;}
      .of-name {font-size:1.55rem;font-weight:800;color:var(--navy);line-height:1.05;}
      .of-tagline {font-size:.86rem;color:var(--muted);margin-top:.22rem;}
      .of-flow {
        display:grid;grid-template-columns:repeat(6,minmax(84px,1fr));gap:.35rem;
        position:relative;padding:.7rem .8rem;margin:.15rem 0 .7rem;
        border:1px solid var(--line);border-radius:17px;background:white;
        box-shadow:0 8px 25px rgba(15,23,42,.045);
      }
      .of-flow::before {
        content:"";position:absolute;left:8%;right:8%;top:1.77rem;height:2px;
        background:linear-gradient(90deg,#bfdbfe,#60a5fa,#5eead4);z-index:0;
      }
      .of-node {position:relative;z-index:1;text-align:center;color:#94a3b8;}
      .of-has-tip {cursor:help;}
      .of-has-tip::after {
        content:attr(data-tip);position:absolute;left:50%;top:calc(100% + .55rem);
        transform:translate(-50%,-.2rem);width:240px;padding:.58rem .68rem;
        border-radius:10px;background:#11213d;color:white;font-size:.72rem;
        font-weight:500;line-height:1.35;text-align:left;box-shadow:0 10px 25px rgba(15,23,42,.2);
        opacity:0;visibility:hidden;transition:.16s ease;pointer-events:none;z-index:100;
      }
      .of-has-tip:hover::after,.of-has-tip:focus-visible::after {
        opacity:1;visibility:visible;transform:translate(-50%,0);
      }
      .of-node:hover {z-index:50;}
      .of-node-icon {
        width:2.2rem;height:2.2rem;border-radius:50%;display:grid;place-items:center;
        margin:0 auto .28rem;background:#f1f5f9;border:3px solid white;
        box-shadow:0 0 0 1px #d9e3ef;transition:.25s ease;
      }
      .of-node-icon .of-svg {width:1.05rem;height:1.05rem;}
      .of-node-label {font-size:.68rem;font-weight:700;line-height:1.1;}
      .of-node.done {color:var(--teal);}
      .of-node.done .of-node-icon {background:#dff8f3;box-shadow:0 0 0 1px #65d9cb;}
      .of-node.active {color:var(--blue);}
      .of-node.active .of-node-icon {
        background:#e5efff;box-shadow:0 0 0 4px #eaf2ff,0 0 16px #93b9ff;
        animation:pulse 1.2s ease-in-out infinite;
      }
      .of-flow.running::after {
        content:"";position:absolute;top:1.61rem;left:7%;width:.34rem;height:.34rem;
        border-radius:50%;background:var(--blue);box-shadow:0 0 10px #60a5fa;
        z-index:2;animation:travel 2.8s ease-in-out infinite;
      }
      .of-note {
        display:flex;gap:.65rem;align-items:flex-start;padding:.72rem .82rem;
        border-radius:13px;background:#f0f6ff;border:1px solid #cfe0fa;
        color:#27466f;font-size:.82rem;line-height:1.4;
      }
      .of-note .of-svg {flex:0 0 auto;margin-top:.08rem;}
      .of-empty {
        min-height:245px;border:1px dashed #cbd8e7;border-radius:17px;background:white;
        display:grid;place-items:center;text-align:center;color:var(--muted);padding:2rem;
      }
      .of-empty-icon {
        width:3.4rem;height:3.4rem;border-radius:16px;display:grid;place-items:center;
        margin:0 auto .75rem;color:var(--blue);background:var(--blue-soft);
      }
      .of-empty-icon .of-svg {width:1.65rem;height:1.65rem;}
      .of-decision {
        display:flex;gap:.75rem;align-items:flex-start;border-radius:15px;
        padding:.8rem .95rem;margin:.2rem 0 .7rem;background:#edf9f4;
        border:1px solid #bde9d6;color:#285947;
      }
      .of-decision.warning {background:#fff8e8;border-color:#f1d498;color:#714b13;}
      .of-decision.error {background:#fff1f1;border-color:#f3c1c1;color:#783636;}
      .of-decision-icon {
        width:2rem;height:2rem;border-radius:9px;display:grid;place-items:center;
        background:rgba(255,255,255,.72);flex:0 0 auto;
      }
      .of-decision-title {font-weight:800;color:var(--navy);margin-bottom:.1rem;}
      .of-agent-grid {display:grid;grid-template-columns:repeat(3,1fr);gap:.7rem;}
      .of-agent {
        border:1px solid var(--line);border-radius:15px;background:white;padding:.8rem;
        min-height:160px;
      }
      .of-agent-head {display:flex;gap:.6rem;align-items:center;margin-bottom:.55rem;}
      .of-avatar {
        width:2.3rem;height:2.3rem;border-radius:11px;display:grid;place-items:center;
        color:var(--blue);background:var(--blue-soft);
      }
      .of-avatar .of-svg {width:1.2rem;height:1.2rem;}
      .of-agent-name {font-weight:800;color:var(--navy);font-size:.9rem;}
      .of-agent-role {font-size:.7rem;color:var(--muted);}
      .of-agent-text {font-size:.8rem;line-height:1.45;color:#334155;}
      .of-term {
        position:relative;display:inline-block;border-bottom:1px dotted currentColor;
        cursor:help;font-weight:650;
      }
      .of-term.of-has-tip::after {top:calc(100% + .35rem);}
      .of-glossary-grid {
        display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:.7rem;
        margin-top:.65rem;
      }
      .of-glossary-card {
        border:1px solid var(--line);border-radius:14px;background:white;padding:.78rem .85rem;
      }
      .of-glossary-category {
        color:var(--blue);font-size:.64rem;font-weight:800;text-transform:uppercase;
        letter-spacing:.06em;margin-bottom:.18rem;
      }
      .of-glossary-title {font-size:.92rem;font-weight:800;color:var(--navy);}
      .of-glossary-text {font-size:.79rem;line-height:1.42;color:#475569;margin-top:.25rem;}
      .of-formula {
        padding:.65rem .8rem;border-radius:11px;background:#f3f7fd;
        border:1px solid #d9e5f4;margin:.35rem 0;color:#29466e;font-size:.86rem;
      }
      .of-danger {
        padding:.75rem .85rem;border-radius:12px;background:#fff1f1;
        border:1px solid #f3c1c1;color:#783636;margin:.45rem 0 .7rem;
      }
      @keyframes pulse {50%{transform:scale(1.08)}}
      @keyframes travel {0%{left:7%;opacity:0}10%{opacity:1}90%{opacity:1}100%{left:92%;opacity:0}}
      @media (max-width:900px) {
        .block-container {padding:.75rem !important;}
        .of-flow {grid-template-columns:repeat(3,1fr);}
        .of-flow::before,.of-flow.running::after {display:none;}
        .of-agent-grid {grid-template-columns:1fr;}
        .of-glossary-grid {grid-template-columns:1fr;}
        .of-has-tip::after {display:none;}
      }
      @media (prefers-reduced-motion:reduce) {
        *,*::before,*::after {
          animation-duration:.01ms !important;
          animation-iteration-count:1 !important;
        }
      }
    </style>
    """,
    unsafe_allow_html=True,
)


SVG_PATHS = {
    "logo": (
        '<circle cx="5" cy="6" r="2"/><circle cx="19" cy="6" r="2"/>'
        '<circle cx="12" cy="18" r="2"/><path d="M7 6h10M6.7 7.6l4.2 8.6M17.3 7.6l-4.2 8.6"/>'
    ),
    "order": '<path d="M6 3h9l3 3v15H6z"/><path d="M15 3v4h4M9 11h6M9 15h6"/>',
    "orchestrate": (
        '<circle cx="5" cy="5" r="2"/><circle cx="19" cy="5" r="2"/>'
        '<circle cx="12" cy="19" r="2"/><path d="M7 5h10M6 7l5 10M18 7l-5 10"/>'
    ),
    "plug": '<path d="M8 3v5M16 3v5M6 8h12v2a6 6 0 0 1-6 6v5M9 21h6"/>',
    "plan": (
        '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9'
        'l.1.1-2.8 2.8-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.6v.2'
        'h-4V21a1.7 1.7 0 0 0-1-1.6 1.7 1.7 0 0 0-1.9.3l-.1.1L4.2 17l.1-.1'
        'a1.7 1.7 0 0 0 .3-1.9A1.7 1.7 0 0 0 3 14H3v-4h.1a1.7 1.7 0 0 0 1.6-1'
        ' 1.7 1.7 0 0 0-.3-1.9L4.2 7 7 4.2l.1.1A1.7 1.7 0 0 0 9 4.6a1.7 1.7 0 0 0 1-1.6'
        'V3h4v.1a1.7 1.7 0 0 0 1 1.6 1.7 1.7 0 0 0 1.9-.3l.1-.1L19.8 7l-.1.1'
        'a1.7 1.7 0 0 0-.3 1.9 1.7 1.7 0 0 0 1.6 1h.1v4H21a1.7 1.7 0 0 0-1.6 1z"/>'
    ),
    "agents": (
        '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/>'
        '<circle cx="9" cy="7" r="4"/>'
        '<path d="M22 21v-2a4 4 0 0 0-3-3.9M16 3.1a4 4 0 0 1 0 7.8"/>'
    ),
    "result": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/>',
    "database": (
        '<ellipse cx="12" cy="5" rx="8" ry="3"/>'
        '<path d="M4 5v6c0 1.7 3.6 3 8 3s8-1.3 8-3V5M4 11v6'
        'c0 1.7 3.6 3 8 3s8-1.3 8-3v-6"/>'
    ),
    "lock": (
        '<rect x="4" y="10" width="16" height="11" rx="2"/>'
        '<path d="M8 10V7a4 4 0 0 1 8 0v3M12 14v3"/>'
    ),
    "check": '<circle cx="12" cy="12" r="9"/><path d="m8 12 2.6 2.6L16 9"/>',
    "factory": '<path d="M3 21V9l6 3V9l6 3V4h6v17zM7 17h2M12 17h2M17 17h2"/>',
    "truck": (
        '<path d="M3 5h11v11H3zM14 9h4l3 3v4h-7z"/>'
        '<circle cx="7" cy="18" r="2"/><circle cx="18" cy="18" r="2"/>'
    ),
    "review": '<circle cx="12" cy="8" r="4"/><path d="M5 21a7 7 0 0 1 14 0M17 11l2 2 3-3"/>',
    "summary": '<path d="M4 4h16v16H4zM8 8h8M8 12h8M8 16h5"/>',
    "person": '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
    "chart": '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
}


def svg_icon(name: str, *, size: int | None = None) -> str:
    style = f' style="width:{size}px;height:{size}px"' if size else ""
    return (
        f'<svg class="of-svg"{style} viewBox="0 0 24 24" aria-hidden="true">'
        f"{SVG_PATHS[name]}</svg>"
    )


DECISION_TEXT = {
    WorkflowDecision.CONFIRMED: ("check", "Auftrag kann bestätigt werden", ""),
    WorkflowDecision.PRODUCTION_REQUIRED: (
        "factory",
        "Interne Produktion und Terminplanung erforderlich",
        "warning",
    ),
    WorkflowDecision.PROCUREMENT_REQUIRED: (
        "truck",
        "Externe Beschaffung und Terminplanung erforderlich",
        "warning",
    ),
    WorkflowDecision.MANUAL_REVIEW: (
        "review",
        "Manuelle Prüfung erforderlich",
        "error",
    ),
}

GERMAN_KEYS = {
    "customer": "Kunde",
    "found": "Gefunden",
    "customer_id": "Kundennummer",
    "name": "Name",
    "credit_status": "Bonitätsstatus",
    "country": "Land",
    "payment_terms_days": "Zahlungsziel in Tagen",
    "stock": "Lagerbestand",
    "product_id": "Produktnummer",
    "product_name": "Produktname",
    "available": "Ausreichend vorhanden",
    "requested_quantity": "Bestellmenge",
    "current_stock": "Aktueller Bestand",
    "missing_quantity": "Fehlmenge",
    "capacity": "Produktionskapazität",
    "possible": "Möglich",
    "required_quantity": "Benötigte Menge",
    "weekly_capacity": "Wochenkapazität",
    "within_week_capacity": "Innerhalb einer Woche produzierbar",
    "working_days_per_week": "Arbeitstage pro Woche",
    "daily_capacity": "Tageskapazität",
    "setup_days": "Rüst- und Planungstage",
    "processing_days": "Reine Produktionstage",
    "production_days": "Gesamte Produktionsdauer in Arbeitstagen",
    "duration_days": "Gewählte Durchlaufzeit in Arbeitstagen",
    "calculation": "Berechnungsweg",
    "procurement": "Beschaffung",
    "required": "Erforderlich",
    "supplier": "Lieferant",
    "maximum_quantity": "Maximale Bezugsmenge",
    "lead_time_days": "Lieferzeit in Arbeitstagen",
    "price": "Preisberechnung",
    "currency": "Währung",
    "unit_price": "Stückpreis",
    "quantity": "Menge",
    "subtotal": "Zwischensumme",
    "discount_rate": "Rabattsatz",
    "total_price": "Gesamtpreis",
    "delivery": "Liefertermin",
    "requested_date": "Gewünschter Liefertermin",
    "planning_date": "Planungsdatum",
    "stock_available": "Ware vollständig auf Lager",
    "date_calculation": "Terminberechnung",
    "promised_date": "Zugesagter Liefertermin",
    "requested_date_met": "Wunschtermin eingehalten",
    "fulfillment_possible": "Vollständige Erfüllung möglich",
    "fulfillment_method": "Gewählter Erfüllungsweg",
    "fulfillment_reason": "Begründung des Erfüllungswegs",
    "decision": "Entscheidung",
    "explanation": "Begründung",
    "processing_seconds": "Verarbeitungszeit in Sekunden",
    "metagpt_used": "MetaGPT verwendet",
    "error": "Fehler",
}

GERMAN_VALUES = {
    "confirmed": "Auftrag bestätigen",
    "production_required": "Interne Produktion erforderlich",
    "procurement_required": "Externe Beschaffung erforderlich",
    "manual_review": "Manuelle Prüfung erforderlich",
    "stock": "Lagerbestand",
    "production": "Interne Produktion",
    "procurement": "Externe Beschaffung",
    "manual": "Manuelle Planung",
}

GLOSSARY = [
    (
        "Grundlagen",
        "Business Process Management (BPM)",
        "BPM gestaltet, steuert und verbessert betriebliche Abläufe. Hier wird die "
        "Auftragsabwicklung als durchgängiger digitaler Prozess gezeigt.",
    ),
    (
        "Grundlagen",
        "Auftragsabwicklung",
        "Alle Schritte vom Eingang eines Kundenauftrags über Prüfung, Bestand, Produktion, "
        "Beschaffung und Preis bis zur Auftragsbestätigung.",
    ),
    (
        "Grundlagen",
        "Workflow",
        "Eine festgelegte Abfolge zusammengehöriger Arbeitsschritte mit Eingaben, Regeln und "
        "Ergebnissen.",
    ),
    (
        "Steuerung",
        "Workflow-Orchestrator",
        "Die zentrale Steuerung. Sie startet die Schritte in der richtigen Reihenfolge, sammelt "
        "Ergebnisse und entscheidet, welcher Prozessweg als Nächstes folgt.",
    ),
    (
        "Agenten",
        "KI-Agent",
        "Eine Softwarekomponente mit klarer Rolle und Aufgabe. Ein Agent erhält Informationen, "
        "führt passende Aktionen aus und gibt sein Ergebnis weiter.",
    ),
    (
        "Agenten",
        "Multi-Agentensystem",
        "Mehrere spezialisierte Agenten arbeiten koordiniert an einem gemeinsamen Ziel, statt "
        "alle Aufgaben in einer einzigen Komponente zu vermischen.",
    ),
    (
        "Agenten",
        "Auftrags-Agent",
        "Prüft die Auftragseingabe und fasst Kunde, Produkt, Menge und Wunschtermin verständlich "
        "zusammen.",
    ),
    (
        "Agenten",
        "Planungs-Agent",
        "Bewertet Bestand, Produktionskapazität und Liefertermin und erklärt den gewählten "
        "Erfüllungsweg.",
    ),
    (
        "Agenten",
        "Beschaffungs-Agent",
        "Prüft, ob eine fehlende Menge vollständig bei einem Lieferanten beschafft werden kann.",
    ),
    (
        "Agenten",
        "Kalkulations-Agent",
        "Berechnet Stückpreis, Zwischensumme, Mengenrabatt und Gesamtpreis anhand fester Regeln.",
    ),
    (
        "Agenten",
        "Validierungs-Agent",
        "Kontrolliert, ob Entscheidung und Erklärung zu den ermittelten Geschäftsdaten passen.",
    ),
    (
        "KI",
        "MetaGPT",
        "Ein Open-Source-Framework für rollenbasierte Multi-Agentensysteme. Im Prototyp erklären "
        "und prüfen seine Rollen das Ergebnis, verändern aber keine Geschäftsdaten.",
    ),
    (
        "KI",
        "LLM / Sprachmodell",
        "Ein KI-Modell, das Sprache verarbeitet und erzeugt. Es formuliert hier verständliche "
        "Erklärungen, ist aber nicht die Quelle für Preise, Bestände oder Termine.",
    ),
    (
        "Integration",
        "MCP",
        "Model Context Protocol: ein standardisiertes Protokoll, über das KI-Anwendungen "
        "Werkzeuge und Datenquellen kontrolliert finden und aufrufen können.",
    ),
    (
        "Integration",
        "MCP-Client",
        "Die anfragende Seite. Der Client sendet einen strukturierten Werkzeugaufruf an den "
        "MCP-Server und nimmt dessen Ergebnis entgegen.",
    ),
    (
        "Integration",
        "MCP-Server",
        "Die anbietende Seite. Der Server stellt definierte Werkzeuge bereit, prüft Parameter "
        "und liefert kontrollierte, strukturierte Ergebnisse zurück.",
    ),
    (
        "Integration",
        "MCP-Werkzeug",
        "Eine klar begrenzte Funktion des MCP-Servers, beispielsweise Kunden abrufen, Bestand "
        "prüfen oder einen Liefertermin berechnen.",
    ),
    (
        "Integration",
        "Schnittstelle / API",
        "Ein festgelegter Zugang, über den Softwaresysteme Daten austauschen oder Funktionen "
        "aufrufen. MCP vereinheitlicht die Nutzung solcher Zugänge für KI-Anwendungen.",
    ),
    (
        "Integration",
        "Strukturierte Daten / JSON",
        "Daten mit eindeutig benannten Feldern. Dadurch können Komponenten Werte zuverlässig "
        "weiterverarbeiten, statt sie aus freiem Text erraten zu müssen.",
    ),
    (
        "Systeme",
        "CRM",
        "Customer Relationship Management: System für Kundenstammdaten, Kontakte und hier auch "
        "den Bonitätsstatus.",
    ),
    (
        "Systeme",
        "ERP",
        "Enterprise Resource Planning: zentrales System für Aufträge, Preise, Materialien, "
        "Finanzen und weitere Unternehmensressourcen.",
    ),
    (
        "Systeme",
        "PPS / MES",
        "PPS plant Produktion und Materialbedarf. MES unterstützt und überwacht die operative "
        "Fertigung. Im Prototyp liefern sie Kapazitätsdaten.",
    ),
    (
        "Systeme",
        "SRM",
        "Supplier Relationship Management: System für Lieferanten, Bezugsgrenzen und "
        "Beschaffungszeiten.",
    ),
    (
        "Fachlichkeit",
        "Bonität",
        "Einschätzung der Zahlungsfähigkeit eines Kunden. Nur ein freigegebener Status erlaubt "
        "die automatische Weiterverarbeitung.",
    ),
    (
        "Fachlichkeit",
        "Stammdaten",
        "Relativ stabile Grunddaten wie Kunden, Produkte, Preise, Kapazitäten und Lieferanten.",
    ),
    (
        "Fachlichkeit",
        "Lagerbestand und Fehlmenge",
        "Der Lagerbestand ist die verfügbare Menge. Die Fehlmenge ist der Teil des Auftrags, "
        "der zusätzlich produziert oder beschafft werden muss.",
    ),
    (
        "Fachlichkeit",
        "Produktionskapazität",
        "Menge, die in einem Zeitraum hergestellt werden kann. Aus Wochenkapazität und "
        "Arbeitstagen berechnet das System die Tageskapazität.",
    ),
    (
        "Fachlichkeit",
        "Rüst- und Planungstage",
        "Zeit für Vorbereitung, Maschinenumstellung und Produktionsplanung, bevor die eigentliche "
        "Fertigung abgeschlossen werden kann.",
    ),
    (
        "Fachlichkeit",
        "Beschaffung",
        "Externer Einkauf einer fehlenden Menge bei einem Lieferanten, wenn die interne "
        "Bereitstellung nicht geeignet ist.",
    ),
    (
        "Fachlichkeit",
        "Durchlaufzeit",
        "Gesamte Zeit vom Planungsbeginn bis zur Bereitstellung, angegeben in Arbeitstagen.",
    ),
    (
        "Fachlichkeit",
        "Wunschtermin und zugesagter Liefertermin",
        "Der Wunschtermin kommt vom Kunden. Der zugesagte Termin ist der früheste tatsächlich "
        "erreichbare Termin nach Bestands-, Produktions- oder Beschaffungsprüfung.",
    ),
    (
        "Qualität",
        "Regelbasierte Entscheidung",
        "Eine reproduzierbare Entscheidung nach festen Bedingungen. Gleiche Eingaben ergeben "
        "dieselbe Entscheidung; das Sprachmodell darf sie nicht verändern.",
    ),
    (
        "Qualität",
        "Validierung",
        "Prüfung, ob Daten, Berechnung, Entscheidung und Erklärung vollständig und "
        "widerspruchsfrei "
        "zusammenpassen.",
    ),
    (
        "Qualität",
        "Prototyp",
        "Eine vereinfachte, funktionsfähige Umsetzung zum Demonstrieren und Evaluieren eines "
        "Konzepts, noch kein produktives Unternehmenssystem.",
    ),
]


def money(value: float | int | None, currency: str = "EUR") -> str:
    if value is None:
        return "–"
    amount = f"{float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{amount} {currency}"


def german_date(value: Any) -> str:
    if not value:
        return "–"
    if isinstance(value, date):
        return value.strftime("%d.%m.%Y")
    try:
        return datetime.fromisoformat(str(value)).strftime("%d.%m.%Y")
    except ValueError:
        return str(value)


def germanise(value: Any, key: str = "") -> Any:
    if isinstance(value, dict):
        return {
            GERMAN_KEYS.get(item_key, item_key): germanise(item_value, item_key)
            for item_key, item_value in value.items()
        }
    if isinstance(value, list):
        return [germanise(item) for item in value]
    if isinstance(value, bool):
        return "Ja" if value else "Nein"
    if value is None:
        return "Nicht erforderlich"
    if isinstance(value, str) and value in GERMAN_VALUES:
        return GERMAN_VALUES[value]
    if isinstance(value, str) and (key.endswith("_date") or key == "planning_date"):
        return german_date(value)
    if key == "discount_rate" and isinstance(value, (float, int)):
        return f"{float(value) * 100:.0f} %"
    return value


def next_identifier(prefix: str, records: dict[str, Any]) -> str:
    numbers = [
        int(match.group(1))
        for identifier in records
        if (match := re.fullmatch(rf"{prefix}(\d+)", identifier))
    ]
    return f"{prefix}{(max(numbers, default=0) // 100 + 1) * 100}"


def option_index(options: dict[str, str], preferred_value: str) -> int:
    values = list(options.values())
    return values.index(preferred_value) if preferred_value in values else 0


def clear_selection_state(kind: str) -> None:
    related_keys = {
        f"edit_{kind}",
        f"delete_{kind}",
        f"confirm_delete_{kind}",
        f"{kind}_action",
    }
    for key in list(st.session_state):
        if (
            str(key).startswith(f"{kind}_")
            or key == f"managed_{kind}"
            or key in related_keys
        ):
            del st.session_state[key]
    st.session_state.pop("last_result", None)


def process_map(active_step: int = 0, *, running: bool = False) -> str:
    nodes = [
        ("order", "Auftrag", "Kunde, Produkt, Menge und Wunschtermin werden erfasst."),
        (
            "orchestrate",
            "Steuerung",
            "Der Workflow-Orchestrator koordiniert Reihenfolge, Agenten und Prozesswege.",
        ),
        (
            "plug",
            "MCP-Daten",
            "Der MCP-Client ruft kontrollierte Werkzeuge des MCP-Servers auf.",
        ),
        (
            "plan",
            "Planung",
            "Bestand, Produktion, Beschaffung, Preis und Liefertermin werden ausgewertet.",
        ),
        (
            "agents",
            "MetaGPT",
            "Spezialisierte KI-Agenten erklären und validieren die feststehenden Ergebnisse.",
        ),
        (
            "result",
            "Ergebnis",
            "Entscheidung, Begründung, Berechnung und Protokoll werden zusammengeführt.",
        ),
    ]
    rendered = []
    for index, (icon, label, description) in enumerate(nodes, start=1):
        state = "done" if index < active_step else "active" if index == active_step else ""
        rendered.append(
            f'<div class="of-node of-has-tip {state}" tabindex="0" '
            f'data-tip="{escape(description, quote=True)}" '
            f'aria-label="{escape(label)}: {escape(description, quote=True)}">'
            '<div class="of-node-icon">'
            f'{svg_icon(icon)}</div><div class="of-node-label">{label}</div></div>'
        )
    running_class = " running" if running else ""
    return f'<div class="of-flow{running_class}">{"".join(rendered)}</div>'


def agent_cards(messages: dict[str, str]) -> str:
    agents = [
        (
            "order_agent",
            "person",
            "Anna",
            "Auftrags-Agentin",
            "Fasst Auftrag, Kunde, Produkt, Menge und Wunschtermin zusammen.",
        ),
        (
            "planning_agent",
            "chart",
            "Paul",
            "Planungs-Agent",
            "Erklärt Lager, Kapazität, Beschaffung, Preis und Liefertermin.",
        ),
        (
            "validation_agent",
            "result",
            "Vera",
            "Validierungs-Agentin",
            "Prüft, ob Entscheidung, Berechnung und Erklärung zusammenpassen.",
        ),
    ]
    cards = []
    for key, icon, name, role, description in agents:
        text = escape(messages.get(key, "Keine Nachricht vorhanden.")).replace("\n", "<br>")
        cards.append(
            f'<div class="of-agent" title="{escape(description, quote=True)}">'
            '<div class="of-agent-head">'
            f'<div class="of-avatar">{svg_icon(icon)}</div><div>'
            f'<div class="of-agent-name">{name}</div>'
            f'<div class="of-agent-role">{role}</div></div></div>'
            f'<div class="of-agent-text">{text}</div></div>'
        )
    return f'<div class="of-agent-grid">{"".join(cards)}</div>'


def calculation_explanation(result: Any) -> None:
    stock = result.stock
    capacity = result.capacity or {}
    procurement = result.procurement or {}
    price = result.price
    delivery = result.delivery
    fulfillment_method = delivery.get("fulfillment_method", "manual")
    requested = int(stock.get("requested_quantity", result.order.quantity))
    current = int(stock.get("current_stock", 0))
    missing = int(stock.get("missing_quantity", 0))

    left, right = st.columns(2)
    with left:
        st.markdown("**Lagerprüfung**")
        st.markdown(
            f'<div class="of-formula">{requested} bestellt − {current} auf Lager '
            f'= <strong>{missing} Stück Fehlmenge</strong></div>',
            unsafe_allow_html=True,
        )
        st.markdown("**Preisberechnung**")
        discount = float(price.get("discount_rate", 0)) * 100
        st.markdown(
            f'<div class="of-formula">{money(price.get("unit_price"))} × '
            f'{price.get("quantity", 0)}; {discount:.0f} % Rabatt → '
            f'<strong>{money(price.get("total_price"))}</strong></div>',
            unsafe_allow_html=True,
        )
    with right:
        if fulfillment_method == "production" and capacity:
            st.markdown("**Produktionsdauer**")
            text = escape(capacity.get("calculation", ""))
        elif fulfillment_method == "procurement" and procurement:
            st.markdown("**Beschaffungsdauer**")
            text = f"Lieferzeit: {procurement.get('lead_time_days', 0)} Arbeitstage"
        elif fulfillment_method == "stock":
            st.markdown("**Bereitstellung**")
            text = "Die vollständige Menge liegt auf Lager."
        else:
            st.markdown("**Manuelle Planung**")
            text = escape(
                delivery.get(
                    "fulfillment_reason",
                    "Kein vollständiger Erfüllungsweg ist automatisch planbar.",
                )
            )
        st.markdown(f'<div class="of-formula">{text}</div>', unsafe_allow_html=True)
        st.markdown("**Liefertermin**")
        st.markdown(
            f'<div class="of-formula">{escape(delivery.get("date_calculation", ""))} '
            f'<strong>{german_date(delivery.get("promised_date"))}</strong></div>',
            unsafe_allow_html=True,
        )


def customer_table(customers: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "Kundennummer": identifier,
            "Unternehmen": record.get("name"),
            "Bonität": record.get("credit_status"),
            "Land": record.get("country"),
            "Zahlungsziel": f"{record.get('payment_terms_days', 0)} Tage",
        }
        for identifier, record in customers.items()
    ]


def product_table(
    products: dict[str, Any],
    capacities: dict[str, Any],
    suppliers: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        {
            "Produktnummer": identifier,
            "Produkt": record.get("name"),
            "Bestand": record.get("stock"),
            "Stückpreis": money(record.get("unit_price")),
            "Wochenkapazität": capacities.get(identifier, {}).get("weekly_capacity", 0),
            "Lieferant": suppliers.get(identifier, {}).get("supplier", "–"),
        }
        for identifier, record in products.items()
    ]


@st.dialog("Begriffe einfach erklärt", width="large")
def glossary_dialog() -> None:
    st.caption(
        "Kurze Erklärungen zu BPM, Agenten, MetaGPT, MCP und den verwendeten Geschäftsdaten"
    )
    search_column, category_column = st.columns([1.6, 1])
    search = search_column.text_input(
        "Begriff suchen",
        placeholder="z. B. MCP-Server, Agent oder Bonität",
        key="glossary_search",
    )
    categories = ["Alle", *sorted({category for category, _, _ in GLOSSARY})]
    category_filter = category_column.selectbox(
        "Themenbereich", categories, key="glossary_category"
    )

    needle = search.strip().casefold()
    matches = [
        (category, title, description)
        for category, title, description in GLOSSARY
        if (category_filter == "Alle" or category == category_filter)
        and (
            not needle
            or needle in title.casefold()
            or needle in description.casefold()
            or needle in category.casefold()
        )
    ]
    if not matches:
        st.info("Zu dieser Suche wurde kein Begriff gefunden.")
        return

    cards = []
    for category, title, description in matches:
        cards.append(
            '<article class="of-glossary-card">'
            f'<div class="of-glossary-category">{escape(category)}</div>'
            f'<div class="of-glossary-title">{escape(title)}</div>'
            f'<div class="of-glossary-text">{escape(description)}</div>'
            "</article>"
        )
    st.markdown(
        f'<div class="of-glossary-grid">{"".join(cards)}</div>',
        unsafe_allow_html=True,
    )


@st.dialog("Stammdatenverwaltung", width="large")
def master_data_dialog() -> None:
    customers = list_customers()
    products = list_products()
    capacities = list_capacity()
    suppliers = list_suppliers()
    customer_options = {
        f"{identifier} · {record['name']}": identifier for identifier, record in customers.items()
    }
    product_options = {
        f"{identifier} · {record['name']}": identifier for identifier, record in products.items()
    }

    st.caption("Lokale Demonstrationsdaten für CRM, Lager, Produktion und Einkauf")
    customer_tab, product_tab = st.tabs(["Kunden", "Produkte"])

    with customer_tab:
        customer_action = st.radio(
            "Aktion",
            ["Übersicht", "Neu anlegen", "Bearbeiten", "Löschen"],
            horizontal=True,
            key="customer_action",
            label_visibility="collapsed",
        )
        if customer_action == "Übersicht":
            st.dataframe(customer_table(customers), width="stretch", hide_index=True)
        elif customer_action == "Neu anlegen":
            with st.form("create_customer", border=False):
                customer_left, customer_right = st.columns(2)
                new_customer_id = customer_left.text_input(
                    "Kundennummer", value=next_identifier("C", customers)
                )
                new_customer_name = customer_right.text_input("Unternehmensname")
                detail_left, detail_center, detail_right = st.columns(3)
                new_credit_status = detail_left.selectbox(
                    "Bonitätsstatus", ["freigegeben", "in Prüfung", "gesperrt"]
                )
                new_country = detail_center.text_input("Ländercode", value="DE")
                new_terms = detail_right.number_input(
                    "Zahlungsziel in Tagen", min_value=0, max_value=365, value=30
                )
                create_customer = st.form_submit_button(
                    "Kunden anlegen", type="primary", width="stretch"
                )
            if create_customer:
                try:
                    identifier = add_customer(
                        new_customer_id,
                        name=new_customer_name,
                        credit_status=new_credit_status,
                        country=new_country,
                        payment_terms_days=int(new_terms),
                    )
                    clear_selection_state("customer")
                    st.session_state["notice"] = f"Kunde {identifier} wurde angelegt."
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
        elif customer_action == "Bearbeiten":
            edit_customer_label = st.selectbox(
                "Kunde auswählen", list(customer_options), key="edit_customer"
            )
            customer_id = customer_options[edit_customer_label]
            record = customers[customer_id]
            with st.form("update_customer", border=False):
                edit_name = st.text_input("Unternehmensname", value=record.get("name", ""))
                edit_left, edit_center, edit_right = st.columns(3)
                credit_values = ["freigegeben", "in Prüfung", "gesperrt"]
                edit_credit = edit_left.selectbox(
                    "Bonitätsstatus",
                    credit_values,
                    index=(
                        credit_values.index(record.get("credit_status"))
                        if record.get("credit_status") in credit_values
                        else 0
                    ),
                )
                edit_country = edit_center.text_input(
                    "Ländercode", value=record.get("country", "DE")
                )
                edit_terms = edit_right.number_input(
                    "Zahlungsziel in Tagen",
                    min_value=0,
                    max_value=365,
                    value=int(record.get("payment_terms_days", 30)),
                )
                save_customer = st.form_submit_button(
                    "Änderungen speichern", type="primary", width="stretch"
                )
            if save_customer:
                try:
                    update_customer(
                        customer_id,
                        name=edit_name,
                        credit_status=edit_credit,
                        country=edit_country,
                        payment_terms_days=int(edit_terms),
                    )
                    clear_selection_state("customer")
                    st.session_state["notice"] = f"Kunde {customer_id} wurde aktualisiert."
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
        else:
            delete_customer_label = st.selectbox(
                "Kunde auswählen", list(customer_options), key="delete_customer"
            )
            customer_id = customer_options[delete_customer_label]
            customer_name = customers[customer_id].get("name", "")
            st.markdown(
                f'<div class="of-danger"><strong>{escape(customer_id)} · '
                f'{escape(customer_name)}</strong><br>Der Kundendatensatz wird dauerhaft aus '
                "den lokalen Demonstrationsdaten entfernt.</div>",
                unsafe_allow_html=True,
            )
            confirm_customer = st.checkbox(
                "Löschen dieses Kunden ausdrücklich bestätigen.",
                key="confirm_delete_customer",
            )
            if st.button(
                "Kunden löschen",
                disabled=not confirm_customer,
                width="stretch",
                key="delete_customer_button",
            ):
                try:
                    delete_customer(customer_id)
                    clear_selection_state("customer")
                    st.session_state["notice"] = f"Kunde {customer_id} wurde gelöscht."
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))

    with product_tab:
        product_action = st.radio(
            "Aktion",
            ["Übersicht", "Neu anlegen", "Bearbeiten", "Löschen"],
            horizontal=True,
            key="product_action",
            label_visibility="collapsed",
        )
        if product_action == "Übersicht":
            st.dataframe(
                product_table(products, capacities, suppliers),
                width="stretch",
                hide_index=True,
            )
        elif product_action == "Neu anlegen":
            with st.form("create_product", border=False):
                identity_left, identity_right = st.columns(2)
                new_product_id = identity_left.text_input(
                    "Produktnummer", value=next_identifier("P", products)
                )
                new_product_name = identity_right.text_input("Produktname")
                basic_left, basic_right = st.columns(2)
                new_stock = basic_left.number_input(
                    "Lagerbestand", min_value=0, max_value=1_000_000, value=0
                )
                new_price = basic_right.number_input(
                    "Stückpreis in EUR", min_value=0.0, value=100.0, step=1.0
                )
                production_left, production_center, production_right = st.columns(3)
                new_capacity = production_left.number_input(
                    "Wochenkapazität", min_value=0, max_value=1_000_000, value=50
                )
                new_setup = production_center.number_input(
                    "Rüst- und Planungstage", min_value=0, max_value=30, value=1
                )
                new_workdays = production_right.number_input(
                    "Arbeitstage pro Woche", min_value=1, max_value=7, value=5
                )
                supplier_left, supplier_center, supplier_right = st.columns(3)
                new_supplier = supplier_left.text_input("Lieferant (optional)")
                new_maximum = supplier_center.number_input(
                    "Maximale Bezugsmenge", min_value=0, value=0
                )
                new_lead_time = supplier_right.number_input(
                    "Lieferzeit in Arbeitstagen", min_value=0, value=0
                )
                create_product = st.form_submit_button(
                    "Produkt anlegen", type="primary", width="stretch"
                )
            if create_product:
                try:
                    identifier = add_product(
                        new_product_id,
                        name=new_product_name,
                        stock=int(new_stock),
                        unit_price=float(new_price),
                        weekly_capacity=int(new_capacity),
                        setup_days=int(new_setup),
                        working_days_per_week=int(new_workdays),
                        supplier=new_supplier,
                        maximum_quantity=int(new_maximum),
                        lead_time_days=int(new_lead_time),
                    )
                    clear_selection_state("product")
                    st.session_state["notice"] = f"Produkt {identifier} wurde angelegt."
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
        elif product_action == "Bearbeiten":
            edit_product_label = st.selectbox(
                "Produkt auswählen", list(product_options), key="edit_product"
            )
            product_id = product_options[edit_product_label]
            record = products[product_id]
            capacity = capacities.get(product_id, {})
            supplier = suppliers.get(product_id, {})
            with st.form("update_product", border=False):
                identity_left, identity_right = st.columns(2)
                edit_product_name = identity_left.text_input(
                    "Produktname", value=record.get("name", "")
                )
                identity_right.text_input(
                    "Produktnummer", value=product_id, disabled=True
                )
                basic_left, basic_right = st.columns(2)
                edit_stock = basic_left.number_input(
                    "Lagerbestand",
                    min_value=0,
                    max_value=1_000_000,
                    value=int(record.get("stock", 0)),
                )
                edit_price = basic_right.number_input(
                    "Stückpreis in EUR",
                    min_value=0.0,
                    value=float(record.get("unit_price", 0.0)),
                    step=1.0,
                )
                production_left, production_center, production_right = st.columns(3)
                edit_capacity = production_left.number_input(
                    "Wochenkapazität",
                    min_value=0,
                    max_value=1_000_000,
                    value=int(capacity.get("weekly_capacity", 0)),
                )
                edit_setup = production_center.number_input(
                    "Rüst- und Planungstage",
                    min_value=0,
                    max_value=30,
                    value=int(capacity.get("setup_days", 0)),
                )
                edit_workdays = production_right.number_input(
                    "Arbeitstage pro Woche",
                    min_value=1,
                    max_value=7,
                    value=int(capacity.get("working_days_per_week", 5)),
                )
                supplier_left, supplier_center, supplier_right = st.columns(3)
                edit_supplier = supplier_left.text_input(
                    "Lieferant", value=supplier.get("supplier", "")
                )
                edit_maximum = supplier_center.number_input(
                    "Maximale Bezugsmenge",
                    min_value=0,
                    value=int(supplier.get("maximum_quantity", 0)),
                )
                edit_lead_time = supplier_right.number_input(
                    "Lieferzeit in Arbeitstagen",
                    min_value=0,
                    value=int(supplier.get("lead_time_days", 0)),
                )
                save_product = st.form_submit_button(
                    "Änderungen speichern", type="primary", width="stretch"
                )
            if save_product:
                try:
                    update_product(
                        product_id,
                        name=edit_product_name,
                        stock=int(edit_stock),
                        unit_price=float(edit_price),
                        weekly_capacity=int(edit_capacity),
                        setup_days=int(edit_setup),
                        working_days_per_week=int(edit_workdays),
                        supplier=edit_supplier,
                        maximum_quantity=int(edit_maximum),
                        lead_time_days=int(edit_lead_time),
                    )
                    clear_selection_state("product")
                    st.session_state["notice"] = f"Produkt {product_id} wurde aktualisiert."
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
        else:
            delete_product_label = st.selectbox(
                "Produkt auswählen", list(product_options), key="delete_product"
            )
            product_id = product_options[delete_product_label]
            product_name = products[product_id].get("name", "")
            st.markdown(
                f'<div class="of-danger"><strong>{escape(product_id)} · '
                f'{escape(product_name)}</strong><br>Produkt, Kapazitäts- und Lieferantendaten '
                "werden gemeinsam entfernt.</div>",
                unsafe_allow_html=True,
            )
            confirm_product = st.checkbox(
                "Löschen dieses Produkts ausdrücklich bestätigen.",
                key="confirm_delete_product",
            )
            if st.button(
                "Produkt löschen",
                disabled=not confirm_product,
                width="stretch",
                key="delete_product_button",
            ):
                try:
                    delete_product(product_id)
                    clear_selection_state("product")
                    st.session_state["notice"] = f"Produkt {product_id} wurde gelöscht."
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))


customers = list_customers()
products = list_products()
metagpt_installed = metagpt_available()
metagpt_ready = metagpt_installed and metagpt_configured()
customer_options = {
    f"{identifier} · {record['name']}": identifier for identifier, record in customers.items()
}
product_options = {
    f"{identifier} · {record['name']}": identifier for identifier, record in products.items()
}

header_left, header_right = st.columns([6.25, 1.75], vertical_alignment="center")
with header_left:
    st.markdown(
        '<div class="of-header"><div class="of-logo">'
        f'{svg_icon("logo")}</div><div><div class="of-name">OrderFlow AI</div>'
        '<div class="of-tagline">Interaktive Auftragsabwicklung mit '
        '<span class="of-term of-has-tip" tabindex="0" '
        'data-tip="Model Context Protocol: standardisierter Zugriff auf Werkzeuge und Daten." '
        'title="Model Context Protocol">MCP</span> und '
        '<span class="of-term of-has-tip" tabindex="0" '
        'data-tip="Framework für spezialisierte KI-Agenten, die Ergebnisse erklären und prüfen." '
        'title="Multi-Agenten-Framework">MetaGPT</span></div>'
        "</div></div>",
        unsafe_allow_html=True,
    )
with header_right:
    glossary_button, master_data_button = st.columns(2)
    if glossary_button.button(
        "Begriffe",
        width="stretch",
        help="Fachbegriffe und technische Komponenten einfach erklären",
        key="open_glossary",
    ):
        glossary_dialog()
    if master_data_button.button(
        "Stammdaten",
        width="stretch",
        help="Kunden, Produkte, Kapazitäten und Lieferanten verwalten",
        key="open_master_data",
    ):
        master_data_dialog()

if notice := st.session_state.pop("notice", None):
    st.toast(notice)

input_column, process_column = st.columns([0.72, 2.28], gap="medium")

with input_column:
    st.subheader("Auftrag erfassen")
    scenario = st.selectbox(
        "Testszenario",
        [
            "Normalfall",
            "Produktion erforderlich",
            "Beschaffung erforderlich",
            "Bonität gesperrt",
            "Eigene Eingabe",
        ],
        help="Wählt passende Beispieldaten für die Präsentation vor.",
    )
    defaults = {
        "Normalfall": ("C100", "P100", 10),
        "Produktion erforderlich": ("C100", "P100", 30),
        "Beschaffung erforderlich": ("C100", "P100", 80),
        "Bonität gesperrt": ("C200", "P100", 10),
        "Eigene Eingabe": ("C300", "P200", 8),
    }
    default_customer, default_product, default_quantity = defaults[scenario]

    with st.form("order_form"):
        customer_label = st.selectbox(
            "Kunde",
            list(customer_options),
            index=option_index(customer_options, default_customer),
            key=f"customer_{scenario}",
            help="Kundenstammdaten und Bonitätsstatus stammen im Prototyp aus dem CRM-Datensatz.",
        )
        product_label = st.selectbox(
            "Produkt",
            list(product_options),
            index=option_index(product_options, default_product),
            key=f"product_{scenario}",
            help="Produktstammdaten enthalten Bestand, Preis, Kapazität und Lieferantenbezug.",
        )
        quantity_column, date_column = st.columns([.65, 1.35])
        quantity = quantity_column.number_input(
            "Menge",
            min_value=1,
            max_value=10_000,
            value=default_quantity,
            step=1,
            key=f"quantity_{scenario}",
            help=(
                "Bestellte Stückzahl; daraus werden Fehlmenge, Preis und "
                "Kapazitätsbedarf ermittelt."
            ),
        )
        requested_date = date_column.date_input(
            "Wunschtermin",
            value=date.today() + timedelta(days=14),
            format="DD.MM.YYYY",
            key=f"date_{scenario}",
            help=(
                "Vom Kunden gewünschter Termin; er kann vom realistisch zugesagten "
                "Termin abweichen."
            ),
        )
        speed = st.select_slider(
            "Ablauf",
            options=["Sofort", "Schnell", "Präsentation"],
            value="Präsentation",
            help=(
                "Steuert nur die sichtbare Geschwindigkeit der Demonstration, "
                "nicht die Berechnung."
            ),
        )
        use_metagpt = st.checkbox(
            "MetaGPT-Erklärung erstellen",
            value=False,
            disabled=not metagpt_ready,
            help=(
                "MetaGPT lässt drei KI-Agenten das regelbasierte Ergebnis erklären und prüfen. "
                "Die Geschäftswerte bleiben unverändert."
            ),
        )
        submitted = st.form_submit_button(
            "Auftrag bearbeiten", type="primary", width="stretch"
        )

    st.markdown(
        f'<div class="of-note">{svg_icon("lock")}<div>'
        '<span class="of-term of-has-tip" tabindex="0" '
        'data-tip="Der MCP-Client ruft definierte Werkzeuge des MCP-Servers auf." '
        'title="Model Context Protocol">MCP</span> liefert kontrollierte Geschäftsdaten. '
        '<span class="of-term of-has-tip" tabindex="0" '
        'data-tip="MetaGPT koordiniert spezialisierte KI-Rollen für Erklärung und Prüfung." '
        'title="Multi-Agenten-Framework">MetaGPT</span> erklärt und prüft, verändert aber keine '
        "Werte.</div></div>",
        unsafe_allow_html=True,
    )

with process_column:
    process_visual = st.empty()
    status_placeholder = st.empty()
    result_placeholder = st.container()
    stored_result = st.session_state.get("last_result")
    process_visual.markdown(
        process_map(6 if stored_result is not None else 1),
        unsafe_allow_html=True,
    )

    if submitted:
        order = OrderRequest(
            customer_id=customer_options[customer_label],
            product_id=product_options[product_label],
            quantity=int(quantity),
            requested_date=requested_date,
        )
        delay = {"Sofort": 0.0, "Schnell": 0.1, "Präsentation": 0.55}[speed]
        with status_placeholder.status(
            "Geschäftsprozess wird ausgeführt", expanded=True
        ) as status:
            progress = st.progress(0, text="Prozess wird vorbereitet")
            current_event = st.empty()
            event_count = [0]

            def show_event(event: Any) -> None:
                event_count[0] += 1
                progress.progress(
                    min(95, event_count[0] * 8),
                    text=f"{event.agent}: {event.action}",
                )
                process_visual.markdown(
                    process_map(min(5, event.step + 1), running=True),
                    unsafe_allow_html=True,
                )
                current_event.markdown(
                    f"**{event.agent} · {event.action}**  \n{event.message}"
                )

            result = asyncio.run(
                run_order_workflow(
                    order,
                    use_metagpt=use_metagpt,
                    event_callback=show_event,
                    demo_delay_seconds=delay,
                )
            )
            progress.progress(100, text="Geschäftsprozess abgeschlossen")
            process_visual.markdown(process_map(6), unsafe_allow_html=True)
            status.update(
                label="Geschäftsprozess abgeschlossen",
                state="complete",
                expanded=False,
            )
            st.session_state["last_result"] = result

    result = st.session_state.get("last_result")
    with result_placeholder:
        if result is None:
            st.markdown(
                '<div class="of-empty"><div><div class="of-empty-icon">'
                f'{svg_icon("summary")}</div><strong>Bereit für die Demonstration</strong><br>'
                "Auftrag auswählen und den Prozess starten.</div></div>",
                unsafe_allow_html=True,
            )
        else:
            icon, title, style = DECISION_TEXT[result.decision]
            st.markdown(
                f'<div class="of-decision {style}"><div class="of-decision-icon">'
                f'{svg_icon(icon)}</div><div><div class="of-decision-title">{title}</div>'
                f'<div>{escape(result.explanation)}</div></div></div>',
                unsafe_allow_html=True,
            )

            metric_columns = st.columns(5)
            metric_columns[0].metric(
                "Bonität",
                result.customer.get("credit_status", "unbekannt"),
                help="Einschätzung der Zahlungsfähigkeit des Kunden.",
            )
            metric_columns[1].metric(
                "Bestand",
                f"{result.stock.get('current_stock', 0)} Stück",
                delta=(
                    None
                    if result.stock.get("available")
                    else f"{result.stock.get('missing_quantity', 0)} fehlen"
                ),
                delta_color="inverse",
                help="Verfügbare Stückzahl; die Differenz zur Bestellung ist die Fehlmenge.",
            )
            metric_columns[2].metric(
                "Durchlaufzeit",
                (
                    "sofort"
                    if result.delivery.get("fulfillment_method") == "stock"
                    else f"{result.delivery.get('duration_days', 0)} Arbeitstage"
                    if result.delivery.get("fulfillment_possible")
                    else "nicht ermittelbar"
                ),
                help="Benötigte Arbeitszeit des ausgewählten Erfüllungswegs.",
            )
            metric_columns[3].metric(
                "Gesamtpreis",
                money(result.price.get("total_price"), result.price.get("currency", "EUR")),
                help="Stückpreis mal Menge abzüglich des regelbasierten Mengenrabatts.",
            )
            metric_columns[4].metric(
                "Liefertermin",
                german_date(result.delivery.get("promised_date")),
                help=(
                    "Frühester zugesagter Termin nach Bestands-, Produktions- oder "
                    "Beschaffungsprüfung."
                ),
            )

            result_tab, calculation_tab, metagpt_tab, mcp_tab, log_tab = st.tabs(
                ["Ergebnis", "Berechnung", "MetaGPT", "MCP-Daten", "Protokoll"]
            )
            with result_tab:
                order_record = products.get(result.order.product_id, {})
                customer_record = customers.get(result.order.customer_id, {})
                result_left, result_right = st.columns(2)
                result_left.markdown(
                    f"**Kunde:** {customer_record.get('name', result.order.customer_id)}  \n"
                    f"**Produkt:** {order_record.get('name', result.order.product_id)}  \n"
                    f"**Menge:** {result.order.quantity} Stück"
                )
                result_right.markdown(
                    f"**Wunschtermin:** {german_date(result.order.requested_date)}  \n"
                    f"**Zusage:** {german_date(result.delivery.get('promised_date'))}  \n"
                    f"**Verarbeitung:** {result.processing_seconds:.2f} Sekunden"
                )
            with calculation_tab:
                calculation_explanation(result)
            with metagpt_tab:
                if result.metagpt_used:
                    st.markdown(agent_cards(result.metagpt_messages), unsafe_allow_html=True)
                elif result.metagpt_summary:
                    st.warning(result.metagpt_summary)
                else:
                    st.caption(
                        "Für diesen Durchlauf wurde keine MetaGPT-Erklärung angefordert."
                    )
            with mcp_tab:
                st.json(
                    germanise(
                        {
                            "customer": result.customer,
                            "stock": result.stock,
                            "capacity": result.capacity,
                            "procurement": result.procurement,
                            "price": result.price,
                            "delivery": result.delivery,
                        }
                    )
                )
            with log_tab:
                level_names = {
                    EventLevel.INFO: "Information",
                    EventLevel.SUCCESS: "Erfolgreich",
                    EventLevel.WARNING: "Hinweis",
                    EventLevel.ERROR: "Fehler",
                }
                st.dataframe(
                    [
                        {
                            "Zeit": event.timestamp.strftime("%H:%M:%S"),
                            "Status": level_names[event.level],
                            "Rolle": event.agent,
                            "Aufgabe": event.action,
                            "Ergebnis": event.message,
                        }
                        for event in result.events
                    ],
                    width="stretch",
                    hide_index=True,
                )
