from __future__ import annotations

import asyncio
from datetime import date, timedelta

import streamlit as st
from dotenv import load_dotenv

from orderflow.data_store import list_customers, list_products
from orderflow.metagpt_agents import metagpt_available, metagpt_configured
from orderflow.models import EventLevel, OrderRequest, WorkflowDecision
from orderflow.workflow import run_order_workflow

load_dotenv()

st.set_page_config(
    page_title="OrderFlow AI",
    page_icon="⚙️",
    layout="wide",
)

st.markdown(
    """
    <style>
      .block-container {padding-top: 1.8rem; padding-bottom: 3rem;}
      [data-testid="stMetricValue"] {font-size: 1.35rem;}
      .orderflow-kicker {color:#657086;font-size:.9rem;margin-bottom:.2rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


def money(value: float | int | None, currency: str = "EUR") -> str:
    if value is None:
        return "–"
    amount = f"{float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{amount} {currency}"


def event_icon(level: EventLevel) -> str:
    return {
        EventLevel.INFO: "🔵",
        EventLevel.SUCCESS: "✅",
        EventLevel.WARNING: "⚠️",
        EventLevel.ERROR: "❌",
    }[level]


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

st.markdown(
    '<div class="orderflow-kicker">BPM · MetaGPT · Model Context Protocol</div>',
    unsafe_allow_html=True,
)
st.title("OrderFlow AI")
st.caption("Interaktiver Prototyp einer agentenbasierten Auftragsabwicklung")

input_column, process_column = st.columns([0.8, 1.7], gap="large")

with input_column:
    st.subheader("Neuer Auftrag")
    scenario = st.selectbox(
        "Testszenario",
        [
            "Normalfall",
            "Produktion erforderlich",
            "Beschaffung erforderlich",
            "Bonität gesperrt",
            "Eigene Eingabe",
        ],
        help="Die ersten drei Szenarien sind für die Demonstration vorbereitet.",
    )

    defaults = {
        "Normalfall": ("C100", "P100", 10),
        "Produktion erforderlich": ("C100", "P100", 30),
        "Beschaffung erforderlich": ("C100", "P100", 80),
        "Bonität gesperrt": ("C200", "P100", 10),
        "Eigene Eingabe": ("C300", "P200", 8),
    }
    default_customer, default_product, default_quantity = defaults[scenario]
    customer_labels = list(customer_options)
    product_labels = list(product_options)
    customer_index = list(customer_options.values()).index(default_customer)
    product_index = list(product_options.values()).index(default_product)

    with st.form("order_form"):
        customer_label = st.selectbox(
            "Kunde",
            customer_labels,
            index=customer_index,
            key=f"customer_{scenario}",
        )
        product_label = st.selectbox(
            "Produkt",
            product_labels,
            index=product_index,
            key=f"product_{scenario}",
        )
        quantity = st.number_input(
            "Menge",
            min_value=1,
            max_value=10_000,
            value=default_quantity,
            step=1,
            key=f"quantity_{scenario}",
        )
        requested_date = st.date_input(
            "Gewünschter Liefertermin",
            value=date.today() + timedelta(days=14),
            key=f"date_{scenario}",
        )
        use_metagpt = st.checkbox(
            "MetaGPT-Review verwenden",
            value=False,
            disabled=not metagpt_ready,
            help=(
                "Benötigt 'make setup-metagpt' und einen API-Schlüssel in "
                "config/config2.yaml. Ohne Review bleibt der Prototyp vollständig funktionsfähig."
            ),
        )
        submitted = st.form_submit_button(
            "Auftrag starten", type="primary", width="stretch"
        )

    st.info(
        "Die Geschäftsdaten werden ausschließlich durch MCP-Werkzeuge ermittelt. "
        "MetaGPT darf Werte erklären, aber nicht verändern.",
        icon="ℹ️",
    )

with process_column:
    st.subheader("Agenten-Workflow")
    status_placeholder = st.empty()
    result_placeholder = st.container()

    if submitted:
        order = OrderRequest(
            customer_id=customer_options[customer_label],
            product_id=product_options[product_label],
            quantity=int(quantity),
            requested_date=requested_date,
        )

        with status_placeholder.status("Workflow wird ausgeführt …", expanded=True) as status:
            progress = st.progress(0, text="Workflow-Orchestrator startet")
            event_count = [0]

            def show_event(event: object) -> None:
                event_count[0] += 1
                progress.progress(
                    min(95, event_count[0] * 10),
                    text=f"{event.agent}: {event.action}",
                )
                st.write(
                    f"{event_icon(event.level)} **{event.agent} · {event.action}** — "
                    f"{event.message}"
                )

            result = asyncio.run(
                run_order_workflow(
                    order,
                    use_metagpt=use_metagpt,
                    event_callback=show_event,
                    demo_delay_seconds=0.12,
                )
            )
            progress.progress(100, text="Workflow abgeschlossen")
            status.update(label="Workflow abgeschlossen", state="complete", expanded=True)
            st.session_state["last_result"] = result

    result = st.session_state.get("last_result")
    with result_placeholder:
        if result is None:
            st.markdown("### Bereit")
            st.write("Links einen Beispielauftrag auswählen und den Workflow starten.")
        else:
            st.markdown("### Entscheidung")
            if result.decision is WorkflowDecision.CONFIRMED:
                st.success("Auftrag kann bestätigt werden.")
            elif result.decision is WorkflowDecision.PRODUCTION_REQUIRED:
                st.warning("Produktion und Terminplanung erforderlich.")
            elif result.decision is WorkflowDecision.PROCUREMENT_REQUIRED:
                st.warning("Externe Beschaffung und Terminplanung erforderlich.")
            else:
                st.error("Manuelle Prüfung erforderlich.")

            st.write(result.explanation)
            if result.metagpt_summary:
                st.markdown("**MetaGPT-Validierung**")
                st.write(result.metagpt_summary)

            metric_columns = st.columns(4)
            metric_columns[0].metric(
                "Bonität",
                result.customer.get("credit_status", "unbekannt"),
            )
            metric_columns[1].metric(
                "Lagerbestand",
                f"{result.stock.get('current_stock', 0)} Stück",
                delta=(
                    None
                    if result.stock.get("available")
                    else f"-{result.stock.get('missing_quantity', 0)} fehlen"
                ),
            )
            metric_columns[2].metric(
                "Gesamtpreis",
                money(result.price.get("total_price"), result.price.get("currency", "EUR")),
            )
            metric_columns[3].metric(
                "Liefertermin",
                result.delivery.get("promised_date", "–"),
            )

            result_tab, mcp_tab, log_tab = st.tabs(
                ["Zusammenfassung", "MCP-Ergebnisse", "Agentenprotokoll"]
            )
            with result_tab:
                st.json(
                    {
                        "decision": result.decision.value,
                        "explanation": result.explanation,
                        "processing_seconds": round(result.processing_seconds, 4),
                        "metagpt_used": result.metagpt_used,
                    }
                )
            with mcp_tab:
                st.json(
                    {
                        "customer": result.customer,
                        "stock": result.stock,
                        "capacity": result.capacity,
                        "procurement": result.procurement,
                        "price": result.price,
                        "delivery": result.delivery,
                    }
                )
            with log_tab:
                st.dataframe(
                    [
                        {
                            "Zeit": event.timestamp.strftime("%H:%M:%S"),
                            "Schritt": event.step,
                            "Agent": event.agent,
                            "Aktion": event.action,
                            "Meldung": event.message,
                        }
                        for event in result.events
                    ],
                    width="stretch",
                    hide_index=True,
                )

st.divider()
with st.expander("Architektur und technische Hinweise"):
    st.graphviz_chart(
        """
        digraph OrderFlow {
          rankdir=LR;
          node [shape=box, style="rounded,filled", fillcolor="#EEF2F7"];
          UI [label="Streamlit UI"];
          O [label="Workflow-Orchestrator"];
          A [label="Agentenkoordination\n(regelbasiert + optional MetaGPT)"];
          C [label="MCP-Client"];
          S [label="MCP-Server"];
          D [label="JSON-Testdaten"];
          UI -> O -> A;
          A -> C -> S -> D;
        }
        """,
        width="stretch",
    )
    st.write("MetaGPT installiert:", "Ja" if metagpt_installed else "Nein")
    st.write("LLM-Zugang konfiguriert:", "Ja" if metagpt_ready else "Nein")

