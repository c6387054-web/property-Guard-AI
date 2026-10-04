"""
PropertyGuard - Frontend (Streamlit)
"""
import os
import html
from datetime import datetime
import streamlit as st
import plotly.graph_objects as go
from fpdf import FPDF

st.set_page_config(page_title="PropertyGuard AI", page_icon="🛡️️", layout="wide")

PAGES = ["Dashboard", "Verify Property", "Verification Results"]
AREA_UNITS = ["Marla", "Kanal", "Sq Ft", "Sq M"]
BACKEND_URL = os.environ.get("PROPERTYGUARD_API", "").rstrip("/")
FORM_KEYS = ["in_title", "in_location", "in_owner", "in_area", "in_unit"]

TONES = {
    "good": ("#116149", "#E6F4EE"),
    "warn": ("#8A5A00", "#FFF3D6"),
    "bad": ("#A3231B", "#FBE7E5"),
}

st.markdown("""
<style>
.pg-header { background: #12263A; border-bottom: 4px solid #B7791F; border-radius: 10px; padding: 1.3rem 1.8rem; margin-bottom: 1.2rem; }
.pg-header h1 { color: #FFFFFF; margin: 0; font-size: 2rem; }
.pg-header p { color: #C9D6E2; margin: 0.25rem 0 0 0; font-size: 1rem; }
.pg-card { border: 1px solid #D9E0E7; border-radius: 10px; padding: 1rem 1.2rem; background: #FFFFFF; color: #12263A; height: 100%; }
.pg-card .label { color: #5B6B7B; font-size: 0.9rem; margin-bottom: 0.3rem; }
.pg-card .value { font-size: 1.35rem; font-weight: 700; margin-bottom: 0.3rem; }
.pg-card .note { color: #5B6B7B; font-size: 0.85rem; }
.pg-badge { display: inline-block; padding: 0.15rem 0.7rem; border-radius: 999px; font-weight: 600; font-size: 0.9rem; }
.pg-issue { border: 1px solid #D9E0E7; border-left-width: 6px; border-radius: 8px; padding: 0.7rem 1rem; margin-bottom: 0.6rem; background: #FFFFFF; color: #12263A; }
.pg-issue .title { font-weight: 700; }
.pg-issue .detail { color: #5B6B7B; font-size: 0.9rem; margin-top: 0.15rem; }
</style>
""", unsafe_allow_html=True)

def make_dummy_results(area: float, unit: str) -> dict:
    doc_area = round(area * 0.85, 2)
    return {
        "is_dummy": True,
        "report_id": "PG-DEMO-" + datetime.now().strftime("%Y%m%d-%H%M%S"),
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "risk_score": 72,
        "document_status": "Partially Verified",
        "document_tone": "warn",
        "document_note": "Document verified with minor OCR ambiguity.",
        "document_area": doc_area,
        "area_unit": unit,
        "area_status": "Mismatch",
        "area_tone": "bad",
        "area_note": f"Declared {area:,.2f} {unit} vs {doc_area:,.2f} {unit} in deed.",
        "duplicate_status": "Possible Duplicate",
        "duplicate_tone": "bad",
        "duplicate_note": "A similar property listing was detected in the database.",
        "issues": [
            {"severity": "High", "title": "Property area mismatch", "detail": "Listing claims 15% more area than registered in the legal deed."},
            {"severity": "High", "title": "Duplicate listing warning", "detail": "Identical property title and location found in registry archive."},
            {"severity": "Medium", "title": "Owner title spelling discrepancy", "detail": "Document deed name differs slightly from the application submission."},
        ],
    }

def fetch_backend_results(data: dict, files) -> dict:
    import requests
    payload = {
        "title": data["title"],
        "location": data["location"],
        "owner": data["owner"],
        "area": str(data["area"]),
        "unit": data["unit"],
    }
    upload = [("documents", (f.name, f.getvalue(), f.type or "application/octet-stream")) for f in files]
    resp = requests.post(f"{BACKEND_URL}/verify", data=payload, files=upload, timeout=180)
    resp.raise_for_status()
    result = resp.json()
    result["is_dummy"] = False
    result.setdefault("report_id", "PG-" + datetime.now().strftime("%Y%m%d-%H%M%S"))
    result.setdefault("generated_at", datetime.now().strftime("%Y-%m-%d %H:%M"))
    result.setdefault("risk_score", 0)
    result.setdefault("issues", [])
    result.setdefault("document_area", None)
    result.setdefault("area_unit", data["unit"])
    for key in ("document", "area", "duplicate"):
        result.setdefault(f"{key}_status", "Unknown")
        result.setdefault(f"{key}_note", "")
        if result.get(f"{key}_tone") not in TONES:
            result[f"{key}_tone"] = "warn"
    return result

def risk_level(score: int):
    if score >= 70:
        return "High Risk", "bad", "#A3231B"
    if score >= 40:
        return "Medium Risk", "warn", "#B7791F"
    return "Low Risk", "good", "#116149"

AREA_TOLERANCE_PCT = 2.0
SEVERITY_COLORS = {"High": "#A3231B", "Medium": "#B7791F", "Low": "#116149"}

def area_comparison(declared: float, document_area):
    if document_area is None:
        return None
    try:
        doc = float(document_area)
    except (TypeError, ValueError):
        return None
    diff = declared - doc
    pct = (abs(diff) / doc * 100) if doc > 0 else 0.0
    return diff, pct, pct <= AREA_TOLERANCE_PCT

def build_risk_gauge(score: int) -> go.Figure:
    _, _, bar_color = risk_level(score)
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            number={"suffix": " / 100", "font": {"size": 34, "color": bar_color}},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": bar_color, "thickness": 0.3},
                "bgcolor": "white",
                "steps": [
                    {"range": [0, 40], "color": "#E6F4EE"},
                    {"range": [40, 70], "color": "#FFF3D6"},
                    {"range": [70, 100], "color": "#FBE7E5"},
                ],
            },
        )
    )
    fig.update_layout(height=230, margin=dict(l=20, r=20, t=30, b=10), paper_bgcolor="rgba(0,0,0,0)")
    return fig

def build_area_chart(declared: float, document_area: float, unit: str, match: bool) -> go.Figure:
    doc_color = "#116149" if match else "#A3231B"
    fig = go.Figure(
        go.Bar(
            x=["Declared (Form)", "Deed Document"],
            y=[declared, document_area],
            marker_color=["#12263A", doc_color],
            text=[f"{declared:,.2f}", f"{float(document_area):,.2f}"],
            textposition="outside",
        )
    )
    fig.update_layout(height=280, margin=dict(l=20, r=20, t=20, b=20), yaxis_title=unit, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", showlegend=False)
    return fig

def pdf_safe(text) -> str:
    return str(text).encode("latin-1", "replace").decode("latin-1")

def build_pdf_report(data: dict, results: dict) -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 22)
    pdf.cell(0, 12, "PropertyGuard AI", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 13)
    pdf.cell(0, 8, "Verification & Fraud Risk Screening Report", new_x="LMARGIN", new_y="NEXT")
    if results.get("is_dummy"):
        pdf.set_font("Helvetica", "I", 10)
        pdf.set_text_color(163, 35, 27)
        pdf.cell(0, 7, "DEMO REPORT - Generated from mock verification data.", new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(0, 0, 0)
    pdf.ln(3)

    def section(title):
        pdf.ln(3)
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 9, pdf_safe(title), new_x="LMARGIN", new_y="NEXT")
        pdf.set_draw_color(183, 121, 31)
        pdf.line(pdf.l_margin, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(2)

    def row(label, value):
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(55, 7, pdf_safe(label))
        pdf.set_font("Helvetica", "", 11)
        pdf.multi_cell(0, 7, pdf_safe(value), new_x="LMARGIN", new_y="NEXT")

    section("Report Details")
    row("Report ID:", results["report_id"])
    row("Generated At:", results["generated_at"])
    section("Property Information")
    row("Title:", data["title"])
    row("Location:", data["location"])
    row("Owner:", data["owner"])
    row("Declared Area:", f"{data['area']:,.2f} {data['unit']}")
    docs = ", ".join(data["documents"]) if data["documents"] else "None"
    row("Uploaded Documents:", docs)
    section("Verification Results")
    label, _, _ = risk_level(results["risk_score"])
    row("Overall Risk:", f"{results['risk_score']} / 100 ({label})")
    row("Document Check:", f"{results['document_status']} - {results['document_note']}")
    row("Area Check:", f"{results['area_status']} - {results['area_note']}")
    cmp_ = area_comparison(data["area"], results.get("document_area"))
    if cmp_:
        diff, pct, match = cmp_
        unit = results.get("area_unit", data["unit"])
        row("Discrepancy:", f"{diff:+,.2f} {unit} ({pct:.1f}%) - {'Match' if match else 'MISMATCH'}")
    row("Duplicate Check:", f"{results['duplicate_status']} - {results['duplicate_note']}")
    section("Detected Red Flags & Issues")
    for i, issue in enumerate(results["issues"], start=1):
        pdf.set_font("Helvetica", "B", 11)
        pdf.multi_cell(0, 7, pdf_safe(f"{i}. [{issue['severity']}] {issue['title']}"), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 6, pdf_safe(issue["detail"]), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)

    return bytes(pdf.output())

def render_header():
    st.markdown("""
    <div class="pg-header">
        <h1>🛡️ PropertyGuard AI</h1>
        <p>Multi-Agent Property Document Verification & Fraud Screening</p>
    </div>
    """, unsafe_allow_html=True)

def status_card(label: str, value: str, tone: str, note: str) -> str:
    color, bg = TONES[tone]
    return f"""
    <div class="pg-card">
        <div class="label">{html.escape(label)}</div>
        <div class="value">
            <span class="pg-badge" style="color:{color}; background:{bg};">{html.escape(value)}</span>
        </div>
        <div class="note">{html.escape(note)}</div>
    </div>
    """

def fill_sample_data():
    st.session_state["in_title"] = "3-Bedroom House, Block C"
    st.session_state["in_location"] = "Gulberg, Lahore"
    st.session_state["in_owner"] = "Ahmed Raza"
    st.session_state["in_area"] = 10.0
    st.session_state["in_unit"] = "Marla"

def run_verification():
    title = st.session_state["in_title"].strip()
    location = st.session_state["in_location"].strip()
    owner = st.session_state["in_owner"].strip()
    area = float(st.session_state["in_area"])
    unit = st.session_state["in_unit"]
    files = st.session_state.get("in_docs") or []

    errors = []
    if not title: errors.append("Please enter the property title.")
    if not location: errors.append("Please enter the location.")
    if not owner: errors.append("Please enter the owner name.")
    if area <= 0: errors.append("Property area must be greater than 0.")
    if not files: errors.append("Please upload at least one deed document (PDF/Image).")

    if errors:
        st.session_state["form_errors"] = errors
        return

    property_data = {"title": title, "location": location, "owner": owner, "area": area, "unit": unit, "documents": [f.name for f in files]}
    if BACKEND_URL:
        try:
            results = fetch_backend_results(property_data, files)
        except Exception as exc:
            st.session_state["form_errors"] = [f"Backend error: {exc}"]
            return
    else:
        results = make_dummy_results(area, unit)

    st.session_state["form_errors"] = []
    st.session_state["property_data"] = property_data
    st.session_state["results"] = results
    st.session_state["page"] = "Verification Results"

def page_dashboard():
    render_header()
    st.subheader("System Overview")
    st.write("PropertyGuard utilizes multi-agent AI to cross-examine real estate listings against legal title documents, catching fraud before deals close.")
    c1, c2, c3 = st.columns(3)
    with c1:
        with st.container(border=True):
            st.markdown("**1. Listing Details**")
            st.caption("Provide claimed title, location, claimed area, and owner identity.")
    with c2:
        with st.container(border=True):
            st.markdown("**2. Document Ingestion**")
            st.caption("Upload property deeds, allotment papers, or registries as PDF/Images.")
    with c3:
        with st.container(border=True):
            st.markdown("**3. Multi-Agent Audit**")
            st.caption("Inspect risk scores, area discrepancy delta charts, and download reports.")
    st.write("")
    if st.button("Start New Verification", type="primary", key="btn_start_new_verification"):
        st.session_state["page"] = "Verify Property"
        st.rerun()

def page_verify():
    render_header()
    st.subheader("Verify Property Claims")
    for err in st.session_state.get("form_errors", []):
        st.error(err)

    with st.container(border=True):
        st.markdown("#### Property Details")
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("Property title", key="in_title", placeholder="e.g. 3-Bedroom House, Block C")
            st.text_input("Claimed owner name", key="in_owner", placeholder="e.g. Ahmed Raza")
        with col2:
            st.text_input("Location / City", key="in_location", placeholder="e.g. Gulberg, Lahore")
            a1, a2 = st.columns([2, 1])
            with a1:
                st.number_input("Claimed area", min_value=0.0, step=1.0, format="%.2f", key="in_area")
            with a2:
                st.selectbox("Unit", AREA_UNITS, key="in_unit")

    with st.container(border=True):
        st.markdown("#### Deed & Document Upload")
        uploaded = st.file_uploader("Upload PDF or image files", type=["pdf", "png", "jpg", "jpeg"], accept_multiple_files=True, key="in_docs")
        if uploaded:
            st.success(f"{len(uploaded)} file(s) attached:")
            for f in uploaded:
                st.write(f"- {f.name} ({f.size / 1024:.1f} KB)")

    b1, b2, _ = st.columns([1, 1, 3])
    with b1:
        st.button("Run Multi-Agent Audit", type="primary", on_click=run_verification)
    with b2:
        st.button("Load Demo Sample", on_click=fill_sample_data)

def page_results():
    render_header()
    st.subheader("Verification Report & Risk Summary")
    if "results" not in st.session_state:
        st.info("No audit running. Please complete the verification form first.")
        if st.button("Go to Verification Form" , key="btn_result _go_to_verification"):
            st.session_state["page"] = "Verify Property"
            st.rerun()
        return

    data = st.session_state["property_data"]
    res = st.session_state["results"]

    if res.get("is_dummy"):
        st.warning("DEMO MODE: Results are simulated for local presentation.")

    with st.container(border=True):
        st.markdown(f"**{data['title']}**")
        st.caption(f"{data['location']} | Declared Owner: {data['owner']} | Stated Area: {data['area']:,.2f} {data['unit']}")

    label, tone, bar_color = risk_level(res["risk_score"])
    color, bg = TONES[tone]
    left, right = st.columns([1, 2])
    with left:
        with st.container(border=True):
            st.markdown("**Overall Fraud Risk**")
            st.plotly_chart(build_risk_gauge(res["risk_score"]))
            st.markdown(f'<div style="text-align:center;"><span class="pg-badge" style="color:{color}; background:{bg};">{label}</span></div>', unsafe_allow_html=True)
    with right:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(status_card("Document Status", res["document_status"], res["document_tone"], res["document_note"]), unsafe_allow_html=True)
        with c2:
            st.markdown(status_card("Area Reconciliation", res["area_status"], res["area_tone"], res["area_note"]), unsafe_allow_html=True)
        with c3:
            st.markdown(status_card("Duplicate Audit", res["duplicate_status"], res["duplicate_tone"], res["duplicate_note"]), unsafe_allow_html=True)

    cmp_ = area_comparison(data["area"], res.get("document_area"))
    if cmp_ is not None:
        diff, pct, match = cmp_
        unit = res.get("area_unit", data["unit"])
        with st.container(border=True):
            m1, m2, m3 = st.columns(3)
            m1.metric("Declared Form Area", f"{data['area']:,.2f} {unit}")
            m2.metric("Document Deed Area", f"{float(res['document_area']):,.2f} {unit}")
            m3.metric("Delta Discrepancy", f"{diff:+,.2f} {unit}", delta=f"{pct:.1f}% mismatch", delta_color="off" if match else "inverse")
            st.plotly_chart(build_area_chart(data["area"], res["document_area"], unit, match))

    st.markdown("#### Categorized Agent Findings")
    for issue in res.get("issues", []):
        sev_color = SEVERITY_COLORS.get(issue["severity"], "#5B6B7B")
        st.markdown(f"""
        <div class="pg-issue" style="border-left-color:{sev_color};">
            <div class="title">{html.escape(issue['title'])} <span style="color:{sev_color}; font-weight:600;">({html.escape(issue['severity'])})</span></div>
            <div class="detail">{html.escape(issue['detail'])}</div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")
    pdf_bytes = build_pdf_report(data, res)
    st.download_button("Download Official Verification Report (PDF)", data=pdf_bytes, file_name="PropertyGuard_Verification_Report.pdf", mime="application/pdf", type="primary")

st.session_state.setdefault("page", "Dashboard")
st.session_state.setdefault("form_errors", [])
st.session_state.setdefault("in_title", "")
st.session_state.setdefault("in_location", "")
st.session_state.setdefault("in_owner", "")
st.session_state.setdefault("in_area", 0.0)
st.session_state.setdefault("in_unit", AREA_UNITS[0])

for _k in FORM_KEYS: st.session_state[_k] = st.session_state[_k]

with st.sidebar:
    st.markdown("## 🛡️ PropertyGuard AI")
    st.radio("Navigation", PAGES, key="page")
    st.divider()
    if BACKEND_URL:
        st.caption(f"Backend Connected: {BACKEND_URL}")
    else:
        st.caption("Running in Standalone Demo Mode")

if st.session_state["page"] == "Dashboard": page_dashboard()
elif st.session_state["page"] == "Verify Property": page_verify()
else: page_results()
