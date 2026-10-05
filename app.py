"""Streamlit demonstration for the Lab 5 multi-agent e-commerce pipeline."""

import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import settings
from core.failure import injector
from security.security_tests import run_security_tests
from workflow.orchestrator import Orchestrator
from workflow.report import build_report, save_report


DEFAULT_QUERY = (
    "Find laptops under ₹70,000 with at least 16 GB RAM, "
    "512 GB storage and rating above 4.2."
)


def _run_workflow(query, mode, approval, injected_failures):
    """Run one coordinated workflow and return its complete shared state."""
    injector.reset()
    for source, failure in injected_failures.items():
        if failure == "permanent":
            injector.add(f"search:{source}", permanent=True)
        elif failure:
            injector.add(f"search:{source}", times=int(failure))
    try:
        return Orchestrator(
            parallel=mode == "parallel",
            approval_mode=approval,
        ).run(query)
    finally:
        injector.reset()


def _run_experiment():
    """Run the documented experiment runner while capturing its table output."""
    from experiments.run_experiment import main as experiment_main

    output = io.StringIO()
    with redirect_stdout(output):
        experiment_main()
    table_path = settings.OUTPUT_DIR / "observation_table.md"
    return output.getvalue(), table_path.read_text(encoding="utf-8")


def _show_state(state):
    report = build_report(state)
    st.subheader("Final recommendation")
    final = state.final_recommendation or {}
    top = final.get("top_recommendation")
    if final.get("status") == "approved" and top:
        st.success(
            f"{top['name']} — Rs.{top['price']:,} "
            f"(score {top['score']}, rating {top['rating']})"
        )
    elif final.get("status") == "rejected":
        st.warning("The human approval gate rejected this recommendation.")
    else:
        st.info(f"Workflow result: {final.get('status', state.status)}")

    st.subheader("Ranked products")
    if state.ranking:
        st.dataframe(
            [
                {
                    "Rank": item["rank"],
                    "Product": item["name"],
                    "Price (Rs.)": item["price"],
                    "RAM (GB)": item["ram_gb"],
                    "Storage (GB)": item["storage_gb"],
                    "Rating": item["rating"],
                    "Score": item["score"],
                    "Why": "; ".join(item["reasons"]),
                }
                for item in state.ranking
            ],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No products were ranked.")

    with st.expander("Requirements and execution plan", expanded=True):
        st.json(
            {
                "sanitized_query": state.sanitized_query,
                "requirements": state.requirements,
                "plan": state.plan,
                "routing": state.routing,
            }
        )

    with st.expander("Agent communication and synchronization"):
        st.dataframe(
            state.messages,
            use_container_width=True,
            hide_index=True,
        )
        st.write("Resolved conflicts")
        st.json(state.conflicts)

    with st.expander("Validation, supervision, approval, and security"):
        st.write("Validation checkpoints")
        st.json(state.validation)
        st.write("Supervisor decision")
        st.json(state.supervisor_decision)
        st.write("Human approval")
        st.json(state.human_approval)
        st.write("Security events")
        st.json(state.security_events or [])
        st.write("Errors")
        st.json(state.errors or [])

    with st.expander("Execution trace and metrics"):
        st.dataframe(
            state.tracer.ordered(),
            use_container_width=True,
            hide_index=True,
        )
        st.json(state.metrics.summary())

    report_path = save_report(state)
    st.download_button(
        "Download workflow report (JSON)",
        data=json.dumps(report, indent=2, ensure_ascii=False, default=str),
        file_name=report_path.name,
        mime="application/json",
    )


def main():
    st.set_page_config(
        page_title="Lab 5 Multi-Agent E-Commerce",
        page_icon="🛒",
        layout="wide",
    )
    st.title("Lab 5: Multi-Agent E-Commerce Analysis")
    st.caption(
        "Planner → Router → parallel Search Agents → Synchronizer → "
        "Filter → Compare → Rank → Validate → Supervisor → Human approval"
    )

    with st.sidebar:
        st.header("Experiment controls")
        query = st.text_area("Product query", DEFAULT_QUERY, height=110)
        mode = st.radio("Execution mode", ["parallel", "sequential"], index=0)
        approval = st.selectbox(
            "Human approval mode",
            ["auto", "reject", "reanalyze_once"],
            help="Interactive console approval is intentionally not used in Streamlit.",
        )
        st.markdown("**Failure injection (optional)**")
        failure_b = st.selectbox("StoreB search", ["none", "1", "2", "permanent"])
        failure_c = st.selectbox("StoreC search", ["none", "1", "2", "permanent"])
        run_clicked = st.button("Run coordinated workflow", type="primary")
        experiment_clicked = st.button("Run full experiment table")
        security_clicked = st.button("Run security tests")

    if run_clicked:
        if not query.strip():
            st.error("Enter a product query before running the workflow.")
        else:
            failures = {
                "StoreB": "" if failure_b == "none" else failure_b,
                "StoreC": "" if failure_c == "none" else failure_c,
            }
            with st.spinner("Coordinating agents and collecting results..."):
                st.session_state["workflow_state"] = _run_workflow(
                    query, mode, approval, failures
                )

    if experiment_clicked:
        with st.spinner("Running sequential, parallel, retry, and security scenarios..."):
            text, table = _run_experiment()
        st.subheader("Observation table")
        st.markdown(table)
        st.download_button(
            "Download observation table",
            data=table,
            file_name="observation_table.md",
            mime="text/markdown",
        )
        with st.expander("Experiment runner console output"):
            st.code(text)

    if security_clicked:
        summary, results = run_security_tests(verbose=False)
        st.subheader("Security test result")
        st.success(summary) if all(item["passed"] for item in results) else st.error(summary)
        st.dataframe(results, use_container_width=True, hide_index=True)

    state = st.session_state.get("workflow_state")
    if state is not None:
        _show_state(state)
    else:
        st.info("Choose controls in the sidebar and run the coordinated workflow.")


if __name__ == "__main__":
    main()
