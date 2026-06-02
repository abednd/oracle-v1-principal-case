"""
Oracle v1 — Streamlit demo UI.

Top: deal input. Below: tabs — the underwriting pack, and a Data-sources view
showing every comparable observation and how each source type is obtained.
Styled to match the Cenotian deck. Calls the SAME oracle.pack.underwriting_pack()
that the API and tests use.

Run:  streamlit run app.py
"""
import json
import pandas as pd
import os
import sys

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from oracle.pack import underwriting_pack
from oracle import data_access

st.set_page_config(page_title="Oracle v1 — Arm Underwriting Intelligence",
                   layout="wide", initial_sidebar_state="collapsed")

# ---------------- Cenotian palette (from the deck) ----------------
PURPLE = "#5B21B6"
PURPLE_DEEP = "#2E1065"
PURPLE_MID = "#7C3AED"
INK = "#1B1525"
MUTED = "#6E6880"
PAPER = "#FFFFFF"
TINT = "#F5F2FB"
VTINT = "#F0EBFB"
LINE = "#E6E1F2"
LILAC = "#9B86D9"

DECISION_COLOR = {
    "go": "#7f9f88",
    "review": "#c39a6b",
    "reject": "#c87878",
}
SEV_COLOR = {
    "info": "#7d748a",
    "caution": "#b8845c",
    "warning": "#b66f73",
}
SEV_ICON = {"info": "\u2022", "caution": "\u25b2", "warning": "\u25a0"}


def gbp(n):
    return f"\u00a3{int(round(n)):,}"


# ---------------- styling ----------------
st.markdown(f"""
<style>
  .stApp {{ background: {PAPER}; }}
  [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{ background: {PAPER}; }}
  [data-testid="stHeader"] {{ height: 0rem; }}
  .block-container {{ max-width: 1200px; padding-top: 3.2rem; padding-bottom: 3rem; }}
  html, body, [class*="css"] {{ font-size: 17px; color: {INK}; }}
  h1, h2, h3, h4 {{ font-family: Georgia, 'Times New Roman', serif !important; color: {INK}; }}

  .oracle-title {{
    text-align: center;
    color: {PURPLE};
    font-size: 22px;
    font-weight: 800;
    letter-spacing: 1.8px;
    text-transform: uppercase;
    margin: 0;
    line-height: 1.05;
  }}

  .oracle-sub {{ text-align:center; color:{INK}; font-size:13px; margin-top:8px; }};
    font-size: 13px;
    margin-top: 8px;
  }}

  .pcase {{ text-align: right; line-height: 1.3; }}
  .pcase .case {{ font-family: Georgia, serif; font-size: 18px; font-weight: 700; color: {PURPLE}; letter-spacing: 1px; text-transform: uppercase; }}
  .pcase .who {{ color: {MUTED}; font-size: 11px; margin-top: 3px; text-transform: uppercase; letter-spacing: 0.7px; }}

  .brand {{ text-align: right; line-height: 1.35; }}
  .brand .name {{ font-family: Georgia, serif; font-size: 17px; font-weight: 700; color: {PURPLE}; letter-spacing: 2px; }}
  .brand .smg {{ color: {MUTED}; font-size: 11px; letter-spacing: 1.5px; }}

  .metric-card {{ padding: 0; }}
  .metric-label {{ font-size: 12px; color: {MUTED}; margin-bottom: 4px; }}
  .metric-value {{ font-size: 22px; line-height: 1.15; color: {INK}; font-weight: 400; white-space: nowrap; }}
  .range-value {{ font-size: 22px; line-height: 1.15; color: {INK}; font-weight: 400; white-space: nowrap; }}

  [data-testid="stMetricValue"] {{
    font-size: 22px !important;
    line-height: 1.15 !important;
    white-space: nowrap !important;
  }}

  [data-testid="stMetricLabel"] {{
    font-size: 12px !important;
  }}

  .sec {{ font-family: Georgia, serif; font-size:21px; font-weight:700; color:{INK}; text-transform:uppercase; letter-spacing:0.7px; border-bottom:1px solid {LINE}; padding-bottom:4px; margin:16px 0 8px 0; }}; text-transform:uppercase; letter-spacing:0.7px; border-bottom:1px solid {LINE}; padding-bottom:4px; margin:16px 0 8px 0; }}; border-bottom: 1px solid {LINE}; padding-bottom: 4px; margin: 16px 0 8px 0; }}
  .pill {{ display:inline-block; padding:2px 10px; border-radius:10px; font-size:12px; background:{VTINT}; color:{PURPLE}; border:1px solid {LINE}; }}
  .hint {{ background:{TINT}; border-left:3px solid {PURPLE_MID}; padding:6px 12px; border-radius:4px; color:{INK}; font-size:13px; margin-top:4px; text-align:center; }}
  .src {{ background:{TINT}; border:1px solid {LINE}; border-radius:6px; padding:10px 14px; margin-bottom:8px; }}
  .src .h {{ font-weight:700; color:{PURPLE}; font-family:Georgia,serif; }}
  .src .code {{ color:{MUTED}; font-size:12px; font-family:monospace; }}

  .stButton > button {{ background:#8f7ab8; color:#ffffff; border:1px solid #7b63a6; font-weight:700; }}
  .stButton > button:hover {{ background:#7b63a6; color:#ffffff; border:1px solid #6b5298; }}

  /* Make Streamlit tabs look like proper clickable tabs */
  [data-baseweb="tab-list"] {{
    gap: 14px !important;
    border-bottom: 1px solid {LINE};
    padding-bottom: 8px;
    margin-top: 16px;
    margin-bottom: 14px;
  }}

  [data-baseweb="tab"] {{
    background: {TINT};
    border: 1px solid {PURPLE_MID};
    border-radius: 10px 10px 0 0;
    padding: 8px 18px !important;
    color: {MUTED};
    font-weight: 600;
  }}

  [data-baseweb="tab"]:hover {{
    background: {VTINT};
    color: {PURPLE};
  }}

  [data-baseweb="tab"][aria-selected="true"] {{
    background: {VTINT};
    border-color: {PURPLE_MID};
    color: {PURPLE};
    box-shadow: inset 0 -3px 0 {PURPLE};
  }}

  [data-baseweb="tab-highlight"] {{
    display: none;
  }}


  .section-banner {{
    text-align: center;
    background: #f2f0f6;
    color: {INK};
    font-family: Georgia, serif;
    font-size: 18px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    border: 1px solid {PURPLE_MID};
    border-radius: 8px;
    padding: 9px 12px;
    margin: 14px 0 14px 0;
  }}


  .decision-rationale {{
    font-size: 16px;
    line-height: 1.45;
    color: {INK};
    margin-top: 6px;
    margin-bottom: 8px;
  }}


  .schema-flow {{
    display: flex;
    align-items: stretch;
    justify-content: space-between;
    gap: 10px;
    margin: 14px 0 18px 0;
  }}

  .schema-step {{
    flex: 1;
    background: #f7f5fa;
    border: 1px solid {PURPLE_MID};
    border-radius: 10px;
    padding: 12px 10px;
    text-align: center;
    min-height: 92px;
  }}

  .schema-step .k {{
    color: {PURPLE};
    font-family: Georgia, serif;
    font-weight: 700;
    font-size: 14px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 6px;
  }}

  .schema-step .d {{
    color: {INK};
    font-size: 13px;
    line-height: 1.35;
  }}

  .schema-arrow {{
    display: flex;
    align-items: center;
    color: {PURPLE};
    font-size: 22px;
    font-weight: 700;
  }}

  .schema-card {{
    background: #fbfafc;
    border: 1px solid {LINE};
    border-left: 4px solid {PURPLE_MID};
    border-radius: 8px;
    padding: 10px 12px;
    margin-bottom: 10px;
    min-height: 108px;
  }}

  .schema-card .name {{
    color: {PURPLE};
    font-family: Georgia, serif;
    font-size: 15px;
    font-weight: 700;
    margin-bottom: 4px;
  }}

  .schema-card .role {{
    color: {INK};
    font-size: 13px;
    line-height: 1.35;
  }}

  .schema-card .fields {{
    color: {MUTED};
    font-size: 12px;
    margin-top: 6px;
    line-height: 1.35;
  }}

  .api-box {{
    background: #f2f0f6;
    border: 1px solid {PURPLE_MID};
    border-radius: 10px;
    padding: 12px 14px;
    margin-top: 12px;
    font-size: 13px;
    line-height: 1.45;
  }}

  /* Final tab styling: centered, clearer, grey-purple */
  [data-baseweb="tab-list"] {{
    justify-content: center !important;
    gap: 18px !important;
    border-bottom: 1px solid {LINE};
    padding-bottom: 10px;
    margin-top: 16px;
    margin-bottom: 16px;
  }}

  [data-baseweb="tab"] {{
    background: #e3deeb !important;
    border: 1px solid {PURPLE_MID} !important;
    border-radius: 10px 10px 0 0 !important;
    padding: 8px 20px !important;
    color: {INK} !important;
    font-weight: 650 !important;
  }}

  [data-baseweb="tab"]:hover {{
    background: #d7cfe3 !important;
    color: {PURPLE} !important;
  }}

  [data-baseweb="tab"][aria-selected="true"] {{
    background: #d0c4df !important;
    border-color: {PURPLE_MID} !important;
    color: {PURPLE} !important;
    box-shadow: inset 0 -3px 0 {PURPLE};
  }}


  /* Force readable text on light background */
  .stMarkdown, .stMarkdown p, .stMarkdown div, .stMarkdown span {{
    color: {INK};
  }}

  label, [data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] p {{
    color: {INK} !important;
    opacity: 1 !important;
  }}

  [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p {{
    color: {MUTED} !important;
    opacity: 1 !important;
  }}

  [data-testid="stMarkdownContainer"] p {{
    color: {INK};
  }}

  [data-testid="stDataFrame"] {{
    color: {INK};
  }}

  /* Keep helper/disclaimer text readable */
  small, .caption, .stCaption {{
    color: {MUTED} !important;
  }}


  /* Force Streamlit widgets back to light styling */
  div[data-baseweb="select"] > div {{
    background-color: #f4f0fa !important;
    color: {INK} !important;
    border: 1px solid {LINE} !important;
  }}

  div[data-baseweb="select"] span {{
    color: {INK} !important;
  }}

  div[data-baseweb="popover"],
  div[data-baseweb="menu"],
  ul[role="listbox"] {{
    background-color: #ffffff !important;
    color: {INK} !important;
  }}

  div[role="option"] {{
    background-color: #ffffff !important;
    color: {INK} !important;
  }}

  div[role="option"]:hover {{
    background-color: #f4f0fa !important;
    color: {PURPLE} !important;
  }}

  input, textarea, .stNumberInput input {{
    background-color: #f4f0fa !important;
    color: {INK} !important;
    border: 1px solid {LINE} !important;
  }}

  button[kind="secondary"], button[aria-label="Increment"], button[aria-label="Decrement"] {{
    background-color: #f4f0fa !important;
    color: {INK} !important;
    border-color: {LINE} !important;
  }}

  [data-testid="stDataFrame"] {{
    background-color: #ffffff !important;
    color: {INK} !important;
  }}

  [data-testid="stDataFrame"] * {{
    color: {INK} !important;
  }}

  /* Dataframe cells / headers in deployed Streamlit */
  .glide-data-grid, .glide-data-grid * {{
    color: {INK} !important;
  }}


  /* Stronger light styling for Streamlit inputs/selects */
  div[data-baseweb="select"] div,
  div[data-baseweb="input"] div,
  div[data-baseweb="base-input"],
  [data-testid="stNumberInput"] div,
  [data-testid="stSelectbox"] div {{
    background-color: #f4f0fa !important;
    color: {INK} !important;
  }}

  div[data-baseweb="select"] *,
  div[data-baseweb="input"] *,
  [data-testid="stNumberInput"] *,
  [data-testid="stSelectbox"] * {{
    color: {INK} !important;
    -webkit-text-fill-color: {INK} !important;
  }}

  input {{
    background-color: #f4f0fa !important;
    color: {INK} !important;
    -webkit-text-fill-color: {INK} !important;
  }}

  div[data-baseweb="popover"] *,
  div[data-baseweb="menu"] *,
  ul[role="listbox"] *,
  div[role="option"] * {{
    background-color: #ffffff !important;
    color: {INK} !important;
    -webkit-text-fill-color: {INK} !important;
  }}

  div[role="option"]:hover,
  div[role="option"]:hover * {{
    background-color: #f4f0fa !important;
    color: {PURPLE} !important;
    -webkit-text-fill-color: {PURPLE} !important;
  }}

  /* Custom light tables */
  .light-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 12px;
    margin-top: 8px;
    margin-bottom: 14px;
    color: {INK};
    background: #ffffff;
    border: 1px solid {LINE};
  }}

  .light-table th {{
    background: #f2f0f6;
    color: {INK};
    font-weight: 700;
    border: 1px solid {LINE};
    padding: 6px 8px;
    text-align: left;
  }}

  .light-table td {{
    background: #ffffff;
    color: {INK};
    border: 1px solid {LINE};
    padding: 6px 8px;
  }}

  .light-table tr:nth-child(even) td {{
    background: #fbfafc;
  }}


  /* Force number input field and +/- controls to light styling */
  [data-testid="stNumberInput"] input {{
    background-color: #f4f0fa !important;
    color: {INK} !important;
    -webkit-text-fill-color: {INK} !important;
  }}

  [data-testid="stNumberInput"] button {{
    background-color: #f4f0fa !important;
    color: {INK} !important;
    border: 1px solid {LINE} !important;
  }}

  [data-testid="stNumberInput"] button:hover {{
    background-color: #e8e1f1 !important;
    color: {PURPLE} !important;
    border-color: {PURPLE_MID} !important;
  }}

  [data-testid="stNumberInput"] button svg,
  [data-testid="stNumberInput"] button path {{
    fill: {INK} !important;
    color: {INK} !important;
    stroke: {INK} !important;
  }}

  [data-testid="stNumberInput"] div {{
    background-color: #f4f0fa !important;
  }}

  [data-testid="stNumberInput"] [data-baseweb="input"] {{
    background-color: #f4f0fa !important;
  }}

  [data-testid="stNumberInput"] [data-baseweb="input"] > div {{
    background-color: #f4f0fa !important;
    border-color: {LINE} !important;
  }}


  /* Final number input contour + JSON toggle styling */
  [data-testid="stNumberInput"] input,
  [data-testid="stNumberInput"] [data-baseweb="input"],
  [data-testid="stNumberInput"] [data-baseweb="input"] > div {{
    background-color: #f4f0fa !important;
    color: {INK} !important;
    -webkit-text-fill-color: {INK} !important;
    border-color: {LINE} !important;
    box-shadow: none !important;
    outline: none !important;
  }}

  [data-testid="stNumberInput"] button {{
    background-color: #f4f0fa !important;
    color: {INK} !important;
    border: 1px solid {LINE} !important;
    box-shadow: none !important;
    outline: none !important;
  }}

  [data-testid="stNumberInput"] button:focus,
  [data-testid="stNumberInput"] button:active,
  [data-testid="stNumberInput"] input:focus {{
    border-color: {LINE} !important;
    box-shadow: 0 0 0 1px {LINE} !important;
    outline: none !important;
  }}

  [data-testid="stNumberInput"] button svg,
  [data-testid="stNumberInput"] button path {{
    fill: {INK} !important;
    stroke: {INK} !important;
    color: {INK} !important;
  }}

  /* Make the Show as JSON toggle purple */
  [data-testid="stToggle"] [role="switch"][aria-checked="true"],
  [data-testid="stToggle"] [aria-checked="true"] {{
    background-color: {PURPLE} !important;
    border-color: {PURPLE} !important;
  }}

  [data-testid="stToggle"] [role="switch"],
  [data-testid="stToggle"] [role="switch"] > div {{
    border-color: {PURPLE_MID} !important;
  }}

  [data-testid="stToggle"] [role="switch"][aria-checked="false"] {{
    background-color: #f4f0fa !important;
  }}


  /* Final hard override: number inputs, select boxes, focus rings */
  [data-testid="stNumberInput"] [data-baseweb="input"],
  [data-testid="stNumberInput"] [data-baseweb="input"] > div,
  [data-testid="stNumberInput"] input,
  [data-testid="stNumberInput"] button,
  [data-testid="stSelectbox"] [data-baseweb="select"],
  [data-testid="stSelectbox"] [data-baseweb="select"] > div {{
    background-color: #f4f0fa !important;
    color: {INK} !important;
    -webkit-text-fill-color: {INK} !important;
    border-color: {LINE} !important;
    box-shadow: none !important;
    outline: none !important;
  }}

  [data-testid="stNumberInput"] [data-baseweb="input"]:focus-within,
  [data-testid="stNumberInput"] [data-baseweb="input"] > div:focus-within,
  [data-testid="stNumberInput"] input:focus,
  [data-testid="stNumberInput"] button:focus,
  [data-testid="stNumberInput"] button:active {{
    border-color: {LINE} !important;
    box-shadow: 0 0 0 1px {LINE} !important;
    outline: none !important;
  }}

  [data-testid="stNumberInput"] button {{
    border-left: 1px solid {LINE} !important;
  }}

  [data-testid="stNumberInput"] button svg,
  [data-testid="stNumberInput"] button path {{
    fill: {INK} !important;
    stroke: {INK} !important;
    color: {INK} !important;
  }}

  /* Remove black browser/autofocus rings inside widgets */
  *:focus {{
    outline-color: {LINE} !important;
  }}

  /* Purple toggle styling - Streamlit uses checkbox-like internals in some versions */
  [data-testid="stToggle"] div[role="switch"],
  [data-testid="stToggle"] button,
  [data-testid="stToggle"] label span {{
    border-color: {PURPLE_MID} !important;
  }}

  [data-testid="stToggle"] div[role="switch"][aria-checked="true"],
  [data-testid="stToggle"] button[aria-checked="true"] {{
    background-color: {PURPLE} !important;
    border-color: {PURPLE} !important;
  }}

  [data-testid="stToggle"] div[role="switch"][aria-checked="false"],
  [data-testid="stToggle"] button[aria-checked="false"] {{
    background-color: #f4f0fa !important;
    border-color: {PURPLE_MID} !important;
  }}

  [data-testid="stToggle"] svg,
  [data-testid="stToggle"] path {{
    fill: {PURPLE} !important;
    stroke: {PURPLE} !important;
  }}
</style>
""", unsafe_allow_html=True)

# ---------------- header: PRINCIPAL CASE + name (left) · CENOTIAN (right) ----------------
h_left, h_mid, h_right = st.columns([1.25, 2.2, 1.15])
with h_left:
    st.markdown(
        '<div class="pcase">'
        '<div class="case">PRINCIPAL CASE</div>'
        '<div class="who">Abdel Hadi Noureddine \u00b7 June 2026</div>'
        '</div>', unsafe_allow_html=True)
with h_mid:
    st.markdown('<div class="oracle-title">ORACLE V1 PROTOTYPE</div>',
                unsafe_allow_html=True)
with h_right:
    st.markdown(
        '<div class="brand">'
        '<div class="name">CENOTIAN</div>'
        '<div class="smg">SPECIAL MISSIONS GROUP</div>'
        '</div>', unsafe_allow_html=True)

st.markdown('<div class="oracle-sub">Internal underwriting tool · asset specs are real · market transactions are synthetic for this case · schema, logic and API surface are production-shaped</div>', unsafe_allow_html=True)
st.markdown("<hr style='border:none;border-top:1px solid %s;margin:10px 0 4px 0;'>" % LINE,
            unsafe_allow_html=True)

assets = data_access.list_assets()
asset_labels = {f"{a['manufacturer']} {a['model']}  ({a['arm_class']}, {a['payload_kg']:.0f}kg)": a["asset_id"]
                for a in assets}
default_idx = (list(asset_labels.values()).index("fanuc_r2000ic_210f")
               if "fanuc_r2000ic_210f" in asset_labels.values() else 0)

# ============================ SECTION 1 — INPUT (top) ============================
# ============================ TABS ============================
st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
tab_pack, tab_sources, tab_how, tab_schema, tab_portfolio = st.tabs([
    "Underwriting pack",
    "Data sources",
    "How Oracle works",
    "Schema / API foundation",
    "Portfolio coverage",
])

# ----------------------------- TAB 1: PACK -----------------------------
with tab_pack:
    st.markdown('<div class="section-banner">DEAL INPUT</div>', unsafe_allow_html=True)

    r1c1, r1c2, r1c3, r1c4 = st.columns(4)
    with r1c1:
        label = st.selectbox("Robotic arm", list(asset_labels.keys()), index=default_idx)
        asset_id = asset_labels[label]
    with r1c2:
        year = st.number_input("Year of manufacture", 2010, 2026, 2021, 1)
    with r1c3:
        condition = st.selectbox("Condition", ["excellent", "good", "fair", "poor"], index=1)
    with r1c4:
        country = st.selectbox("Location", ["GB", "DE", "US", "IT", "FR", "JP", "ES", "PL", "MX", "BR", "IN", "AE"], index=0)

    hours = st.slider("Operating hours", 0, 80000, 12000, 1000)
    r2c1, r2c2, r2c3, r2c4 = st.columns(4)
    with r2c1:
        financing = st.number_input("Requested financing (GBP)", 0, 400000, 40000, 1000)
    with r2c2:
        project_cost = st.number_input("Total project cost (GBP)", 0, 2000000, 280000, 5000)
    with r2c3:
        term = st.number_input("Term (months)", 12, 120, 48, 6)
    with r2c4:
        industry = st.selectbox("End-customer industry",
                                ["packaging", "automotive", "logistics", "general_manufacturing",
                                 "aerospace", "medical", "semiconductor", "food_grade"], index=0)

    st.markdown('<div class="hint">Tip — raise operating hours (try 45,000) or pick a thin-market location '
                '(e.g. BR), then regenerate, to watch the underwriting decision change.</div>',
                unsafe_allow_html=True)

    run = st.button("Generate underwriting pack", type="primary", use_container_width=True)

    # compute (persist across reruns)
    if run or "pack" not in st.session_state:
        deal = dict(asset_id=asset_id, year_of_manufacture=int(year), operating_hours=float(hours),
                    condition_grade=condition, location_country=country,
                    requested_financing_amount=float(financing), total_project_cost=float(project_cost),
                    requested_term_months=int(term), end_customer_industry=industry, currency="GBP")
        if run and "pack" in st.session_state:
            st.session_state["previous_pack"] = st.session_state["pack"]
        st.session_state["pack"] = underwriting_pack(deal)

    pack = st.session_state["pack"]
    v, l, r, a = pack["valuation"], pack["ltv"], pack["recovery"], pack["asset_profile"]

    st.markdown('<div class="section-banner">ORACLE UNDERWRITING OUTPUT</div>', unsafe_allow_html=True)

    show_json = st.toggle("Show as JSON / API payload", value=False)

    if show_json:
        st.markdown("**`POST /underwriting-pack` → response**")
        st.code(json.dumps(pack, indent=2), language="json")
    else:
        col = DECISION_COLOR.get(l["decision"], "#333")
        st.markdown(
            f"<div style='background:{col};color:#fff;padding:12px 18px;border-radius:6px;"
            f"font-size:21px;font-weight:700;line-height:1.4;'>DECISION: {l['decision'].upper()}"
            f"<span style='font-weight:400;font-size:16px;'> &nbsp;·&nbsp; {l['rationale']}</span></div>",
            unsafe_allow_html=True
        )

        st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

        st.markdown('<div class="sec">Asset profile</div>', unsafe_allow_html=True)
        st.write(
            f"**{a['manufacturer']} {a['model']}** · {a['series']} · {a['arm_class']} · "
            f"{a['payload_kg']:.0f}kg payload · {a['reach_mm']:.0f}mm reach · {a['axes']} axes · "
            f"controller {a['controller_family']} · intro {a['year_introduced']} · "
            f"secondary-market liquidity: **{a['secondary_market_liquidity']}**"
        )

        st.markdown('<div class="sec">Valuation</div>', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("FMV central", gbp(v["fmv_central"]))
        c2.markdown(
            f"<div class='metric-card'>"
            f"<div class='metric-label'>Valuation range</div>"
            f"<div class='range-value'>{gbp(v['fmv_low'])} – {gbp(v['fmv_high'])}</div>"
            f"</div>",
            unsafe_allow_html=True
        )
        c3.metric("Confidence", f"{v['confidence_score']} ({v['confidence_band']})")
        c4.metric("Comps used", v["comp_count"])

        adj = v["adjustments"]
        st.caption(
            f"Adjustments applied — age ×{adj['age']} · condition ×{adj['condition']} · "
            f"hours ×{adj['hours']} · geography ×{adj['geography']} · generation ×{adj['generation']} "
            f"· method: {v['method']}"
        )

        st.markdown(
            f"""
            <div style="font-size:13px; color:#6f687d; margin-top:8px; margin-bottom:12px; line-height:1.55;">
              <div><b style="color:{PURPLE};">Age</b> comes from the age-retention curve; older arms receive lower retention factors.</div>
              <div><b style="color:{PURPLE};">Condition</b> uses grade multipliers: good = baseline, excellent premium, fair/poor discount.</div>
              <div><b style="color:{PURPLE};">Hours</b> comes from a wear curve; higher operating hours reduce value like equipment mileage.</div>
              <div><b style="color:{PURPLE};">Geography</b> applies market-liquidity multipliers; mature resale markets receive less/no discount.</div>
              <div><b style="color:{PURPLE};">Generation</b> applies obsolescence penalties for older controllers or discontinued model families.</div>
              <div><b style="color:{PURPLE};">Method</b> shows whether valuation used comparable observations or a fallback depreciation curve.</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        if v["comps_used"]:
            st.markdown(
                "<span class='pill'>Comparable observations used for this valuation</span>",
                unsafe_allow_html=True
            )
            st.markdown(
                pd.DataFrame(v["comps_used"]).to_html(index=False, classes="light-table", border=0),
                unsafe_allow_html=True
            )

        st.markdown('<div class="sec">LTV Recommendation</div>', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Recommended LTV", f"{l['recommended_ltv_pct']}%")
        c2.metric("Requested LTV", f"{l['requested_ltv_pct']}%")
        c3.metric("Max LTV (ceiling)", f"{l['max_ltv_pct']}%")
        c4.metric("Advance recommended", gbp(l["advance_recommended"]))

        st.markdown('<div class="sec">Recovery</div>', unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Base recovery", gbp(r["base_recovery_value"]), f"-{r['base_haircut_pct']}% haircut", delta_color="off")
        c2.metric("Stress recovery", gbp(r["stress_recovery_value"]), f"-{r['stress_haircut_pct']}% haircut", delta_color="off")
        c3.metric("Time-to-sell", f"{r['time_to_sell_months_base']:.0f}–{r['time_to_sell_months_stress']:.0f} mo")
        c4.metric("Preferred path", r["preferred_path"])

        cov = r["stress_covers_financing"]
        cov_color = DECISION_COLOR["go"] if cov else DECISION_COLOR["reject"]
        st.markdown(
            f"Stress recovery vs requested financing: "
            f"<b style='color:{cov_color}'>{'covers' if cov else 'does NOT cover'}</b> "
            f"({gbp(r['stress_recovery_value'])} vs {gbp(pack['inputs']['requested_financing_amount'])})",
            unsafe_allow_html=True
        )

        st.markdown(
            f"""
            <div style="font-size:13px; color:#6f687d; margin-top:10px; margin-bottom:12px; line-height:1.55;">
              <div><b style="color:{PURPLE};">Base recovery</b> estimates what Cenotian could recover through an orderly resale or redeployment path.</div>
              <div><b style="color:{PURPLE};">Stress recovery</b> applies a harsher haircut to test whether the collateral still protects the financing in a downside case.</div>
              <div><b style="color:{PURPLE};">Time-to-sell</b> is based on secondary-market liquidity and comparable depth.</div>
              <div><b style="color:{PURPLE};">Preferred path</b> is redeployment when the robot is liquid and reusable across applications; otherwise liquidation is assumed.</div>
            </div>
            """,
            unsafe_allow_html=True
        )


        if "previous_pack" in st.session_state:
            prev = st.session_state["previous_pack"]
            curr = pack

            prev_inputs = prev.get("inputs", {})
            curr_inputs = curr.get("inputs", {})

            changed = []
            labels = {
                "asset_id": "Robotic arm",
                "year_of_manufacture": "Year",
                "operating_hours": "Operating hours",
                "condition_grade": "Condition",
                "location_country": "Location",
                "requested_financing_amount": "Requested financing",
                "requested_term_months": "Term",
                "end_customer_industry": "End-customer industry",
            }

            for key, label in labels.items():
                if prev_inputs.get(key) != curr_inputs.get(key):
                    changed.append(f"{label}: {prev_inputs.get(key)} → {curr_inputs.get(key)}")

            change_text = "; ".join(changed) if changed else "No input changed since the previous generated scenario."

            st.markdown('<div class="sec">Scenario comparison</div>', unsafe_allow_html=True)
            st.markdown(
                f"<div style='font-size:13px; color:{MUTED}; margin-bottom:8px;'>"
                f"<b style='color:{PURPLE};'>Change tested:</b> {change_text}</div>",
                unsafe_allow_html=True
            )

            comparison_rows = [
                {
                    "Metric": "Decision",
                    "Previous": prev["ltv"]["decision"].upper(),
                    "Current": curr["ltv"]["decision"].upper(),
                    "Impact": f"{prev['ltv']['decision'].upper()} → {curr['ltv']['decision'].upper()}",
                },
                {
                    "Metric": "FMV central",
                    "Previous": gbp(prev["valuation"]["fmv_central"]),
                    "Current": gbp(curr["valuation"]["fmv_central"]),
                    "Impact": gbp(curr["valuation"]["fmv_central"] - prev["valuation"]["fmv_central"]),
                },
                {
                    "Metric": "Recommended LTV",
                    "Previous": f"{prev['ltv']['recommended_ltv_pct']}%",
                    "Current": f"{curr['ltv']['recommended_ltv_pct']}%",
                    "Impact": f"{curr['ltv']['recommended_ltv_pct'] - prev['ltv']['recommended_ltv_pct']:+.1f} pts",
                },
                {
                    "Metric": "Requested LTV",
                    "Previous": f"{prev['ltv']['requested_ltv_pct']}%",
                    "Current": f"{curr['ltv']['requested_ltv_pct']}%",
                    "Impact": f"{curr['ltv']['requested_ltv_pct'] - prev['ltv']['requested_ltv_pct']:+.1f} pts",
                },
                {
                    "Metric": "Stress recovery",
                    "Previous": gbp(prev["recovery"]["stress_recovery_value"]),
                    "Current": gbp(curr["recovery"]["stress_recovery_value"]),
                    "Impact": gbp(curr["recovery"]["stress_recovery_value"] - prev["recovery"]["stress_recovery_value"]),
                },
            ]

            st.markdown(
                pd.DataFrame(comparison_rows).to_html(index=False, classes="light-table", border=0),
                unsafe_allow_html=True
            )
            st.caption("This comparison proves the live mechanism: when an asset-risk input changes, Oracle updates valuation, LTV, recovery and the underwriting decision.")


        st.markdown('<div class="sec">Risk flags</div>', unsafe_allow_html=True)
        if pack["risk_flags"]:
            for f in pack["risk_flags"]:
                c = SEV_COLOR.get(f["severity"], MUTED)
                st.markdown(
                    f"<span style='color:{c};font-weight:700'>{SEV_ICON.get(f['severity'],'•')} "
                    f"{f['flag_type']}</span> <span style='color:{MUTED}'>({f['severity']})</span> — "
                    f"{f['message']}",
                    unsafe_allow_html=True
                )
        else:
            st.markdown("_None._")

        st.caption(pack["disclaimer"])

# ----------------------------- TAB 2: DATA SOURCES -----------------------------

with tab_how:
    st.markdown('<div class="section-banner">HOW ORACLE WORKS</div>', unsafe_allow_html=True)

    st.markdown('<div class="sec">How the prototype works</div>', unsafe_allow_html=True)

    st.markdown("""
**Oracle v1 is not a robot database.** It is a lightweight underwriting intelligence layer.

The prototype takes one robotic-arm-backed deal and converts asset evidence into an underwriting decision:
**valuation → confidence → LTV → recovery → GO / REVIEW / REJECT**.
""")

    st.markdown("""
### 1. What the underwriter inputs
The underwriter enters the robotic arm, year of manufacture, operating hours, condition, location, requested financing, project cost, term, and end-customer industry.

Only the **robotic arm collateral** is deeply valued in v1. Other deal fields are used to create basic risk flags and to show where Oracle plugs into the wider underwriting workflow.
""")

    st.markdown("""
### 2. How Oracle estimates value
Oracle looks up the selected robot in the asset registry, then pulls comparable market observations for that model or similar arms.

It adjusts the value for:
- **age** — older arms generally retain less value;
- **condition** — excellent/good/fair/poor changes the expected resale value;
- **operating hours** — high usage reduces value and can trigger a risk flag;
- **geography** — mature markets are easier to resell into than thin markets;
- **generation/controller** — older or discontinued generations may carry obsolescence risk.

The output is not one false-precise number. It is a **valuation range** with a **confidence score**.
""")

    st.markdown("""
### 3. How confidence affects the underwriting decision
Confidence is based on the quality of the evidence behind the valuation.

Oracle gives higher confidence when there are enough recent, relevant, independent comparables.  
It gives lower confidence when comps are thin, old, volatile, or concentrated in one source.

That matters because a low-confidence valuation should not support the same LTV as a high-confidence valuation.
""")

    st.markdown("""
### 4. How Oracle recommends LTV
Oracle translates valuation and confidence into a recommended LTV.

In simple terms:
- stronger collateral evidence → higher allowable LTV;
- weaker evidence, high hours, thin comps, or obsolete generation → lower LTV;
- if the requested financing is above what the evidence supports, the decision moves from **GO** to **REVIEW** or **REJECT**.

This is the core underwriting change: Oracle does not just show information — it changes the financing decision.
""")

    st.markdown("""
### 5. Why recovery is first-class
Cenotian is financing an asset-backed product, so the real question is not only “what is the robot worth today?”

It is also:

> If the deal goes wrong, what can Cenotian recover?

Oracle therefore calculates a simple **base recovery** and **stress recovery** view, including haircuts and time-to-sell assumptions.  
The key check is whether stress recovery can cover the requested financing amount.
""")

    st.markdown("""
### 6. The proof point in the demo
The demo starts with a clean baseline case where Oracle returns **GO**.

Then you change one real asset-risk input — for example, operating hours from **12,000** to **45,000**.

Oracle reacts by:
- reducing the valuation;
- increasing the requested LTV;
- adding risk flags;
- lowering recovery confidence;
- changing the decision to **REVIEW** or **REJECT**.

That is the bet being proven: **better asset intelligence changes underwriting behavior.**
""")

    st.markdown("""
### 7. Why this is production-shaped
The Streamlit interface is only a thin demo layer. The important foundation is underneath:

- an asset registry;
- comparable market observations;
- valuation and confidence logic;
- LTV Recommendation rules;
- recovery assumptions;
- risk flags;
- a JSON/API-shaped underwriting pack.

In production, the synthetic transaction table would be replaced by real dealer listings, auction results, broker quotes, OEM refurb data, Cenotian deal history, and recovery outcomes.
""")

    st.markdown("""
### What this proves
Oracle v1 proves the first version of the bet because it shows that Cenotian can turn robotic-arm asset evidence into faster, more consistent, and more defensible underwriting decisions.

It does **not** prove the final valuation model is perfect.  
It proves the operating system is buildable: the schema, logic, workflow, and API surface that a real team could take into production.
""")


with tab_sources:
    st.markdown('<div class="section-banner">DATA SOURCES</div>', unsafe_allow_html=True)

    st.markdown('<div class="sec">How the comparable data is sourced</div>', unsafe_allow_html=True)
    st.caption("Transactions are synthetic for this case. Below is how each source type would be "
               "obtained in production, and the full set of observations the engine draws on.")
    for code, title, desc in data_access.SOURCE_LEGEND:
        st.markdown(f"<div class='src'><span class='h'>{title}</span> "
                    f"<span class='code'>({code})</span><br>{desc}</div>", unsafe_allow_html=True)

    all_df = data_access.all_comps()
    st.markdown('<div class="sec">All comparable observations</div>', unsafe_allow_html=True)
    cs1, cs2, cs3 = st.columns(3)
    cs1.metric("Total observations", len(all_df))
    cs2.metric("Models covered", all_df["model_name"].nunique())
    cs3.metric("Source types", all_df["source_type"].nunique())

    # optional filters
    f1, f2 = st.columns(2)
    with f1:
        model_pick = st.selectbox("Filter by model", ["(all)"] + sorted(all_df["model_name"].unique().tolist()))
    with f2:
        src_pick = st.selectbox("Filter by source type", ["(all)"] + sorted(all_df["source_type"].unique().tolist()))
    view = all_df.copy()
    if model_pick != "(all)":
        view = view[view["model_name"] == model_pick]
    if src_pick != "(all)":
        view = view[view["source_type"] == src_pick]
    st.markdown(view.to_html(index=False, classes="light-table", border=0), unsafe_allow_html=True)
    st.caption(f"Showing {len(view)} of {len(all_df)} observations. "
               "reliability_weight (0\u20131) is how much each source is trusted in the weighted valuation.")


# ----------------------------- TAB 4: SCHEMA / API FOUNDATION -----------------------------
with tab_schema:
    st.markdown('<div class="section-banner">SCHEMA / API FOUNDATION</div>', unsafe_allow_html=True)

    st.markdown(
        """
        Oracle is built as a decision engine, not a screen. The schema separates the core objects:
        **assets**, **market observations**, **deal inputs**, **valuation**, **LTV**, **recovery**, and **risk flags**.
        The final output is one API-shaped underwriting pack.
        """
    )

    st.markdown(
        f"""
        <div class="schema-flow">
          <div class="schema-step">
            <div class="k">1. Asset registry</div>
            <div class="d">What robot is being financed?</div>
          </div>
          <div class="schema-arrow">→</div>
          <div class="schema-step">
            <div class="k">2. Market observations</div>
            <div class="d">What comparable evidence supports value?</div>
          </div>
          <div class="schema-arrow">→</div>
          <div class="schema-step">
            <div class="k">3. Valuation + confidence</div>
            <div class="d">What is the arm worth, and how sure are we?</div>
          </div>
          <div class="schema-arrow">→</div>
          <div class="schema-step">
            <div class="k">4. LTV + recovery</div>
            <div class="d">How much can Cenotian safely finance?</div>
          </div>
          <div class="schema-arrow">→</div>
          <div class="schema-step">
            <div class="k">5. Underwriting pack</div>
            <div class="d">GO / REVIEW / REJECT with evidence.</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    c1, c2 = st.columns(2)

    with c1:
        st.markdown(
            f"""
            <div class="schema-card">
              <div class="name">assets</div>
              <div class="role">Robot model registry. This is the real spec spine of Oracle.</div>
              <div class="fields">Key fields: manufacturer, model, series, payload, reach, axes, controller, year introduced, liquidity.</div>
            </div>

            <div class="schema-card">
              <div class="name">market_observations</div>
              <div class="role">Comparable market evidence used to estimate value.</div>
              <div class="fields">Key fields: observed price, source type, condition, hours, age, geography, reliability weight. Synthetic in this case.</div>
            </div>

            <div class="schema-card">
              <div class="name">deals + deal_assets</div>
              <div class="role">The underwriting input: the specific arm-backed deal being assessed.</div>
              <div class="fields">Key fields: requested financing, project cost, term, location, condition, hours, service contract.</div>
            </div>

            <div class="schema-card">
              <div class="name">valuations</div>
              <div class="role">Oracle’s estimate of fair market value and uncertainty.</div>
              <div class="fields">Key fields: FMV low / central / high, confidence score, comp count, age / condition / hours / geography adjustments.</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c2:
        st.markdown(
            f"""
            <div class="schema-card">
              <div class="name">ltv_recommendations</div>
              <div class="role">Turns valuation and confidence into a financing recommendation.</div>
              <div class="fields">Key fields: recommended LTV, requested LTV, max LTV, decision, rationale.</div>
            </div>

            <div class="schema-card">
              <div class="name">recovery_assumptions</div>
              <div class="role">Tests downside protection if the deal goes wrong.</div>
              <div class="fields">Key fields: base recovery, stress recovery, haircuts, time-to-sell, preferred path, recovery confidence.</div>
            </div>

            <div class="schema-card">
              <div class="name">risk_flags</div>
              <div class="role">Explains why the decision tightens or needs review.</div>
              <div class="fields">Examples: high hours, thin comps, geography illiquid, high requested LTV, stress recovery shortfall.</div>
            </div>

            <div class="schema-card">
              <div class="name">underwriting_pack JSON</div>
              <div class="role">The API-shaped output consumed by the UI, future services, or other teams.</div>
              <div class="fields">Combines asset profile, valuation, LTV, recovery, flags, rationale, and data disclaimer.</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown(
        f"""
        <div class="api-box">
          <b style="color:{PURPLE};">Why this matters:</b>
          the Streamlit interface is only a thin layer. The real product foundation is the schema and
          <code>POST /underwriting-pack</code> style output underneath. In production, the synthetic
          market observations would be replaced with dealer feeds, auction results, broker quotes,
          Cenotian deal history, and actual recovery outcomes — while the same schema and decision logic remain usable.
        </div>
        """,
        unsafe_allow_html=True
    )


# ----------------------------- TAB 5: PORTFOLIO COVERAGE -----------------------------
with tab_portfolio:
    st.markdown('<div class="section-banner">PORTFOLIO COVERAGE</div>', unsafe_allow_html=True)

    st.markdown(
        """
        This view shows whether Oracle is only working for one demo asset, or whether the data foundation
        is broad enough to support a portfolio of robotic-arm-backed deals. In production, this is how Cenotian
        would see which robot families are well-covered and which are still too thin for confident underwriting.
        """
    )

    assets_list = data_access.list_assets()
    comps_df = data_access.all_comps()

    total_models = len(assets_list)
    total_obs = len(comps_df)
    covered_models = comps_df["model_name"].nunique() if "model_name" in comps_df.columns else 0
    avg_obs = round(total_obs / max(covered_models, 1), 1)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Robot models", total_models)
    c2.metric("Models with comps", covered_models)
    c3.metric("Comparable observations", total_obs)
    c4.metric("Avg comps / model", avg_obs)

    st.markdown('<div class="sec">Coverage by model</div>', unsafe_allow_html=True)

    if "model_name" in comps_df.columns:
        # Build portfolio coverage table robustly across possible comp schemas
        id_col = "obs_id" if "obs_id" in comps_df.columns else comps_df.columns[0]
        price_col = "observed_price" if "observed_price" in comps_df.columns else None
        source_col = "source_type" if "source_type" in comps_df.columns else None

        agg_spec = {"comp_count": (id_col, "count")}
        if price_col:
            agg_spec.update({
                "avg_price": (price_col, "mean"),
                "min_price": (price_col, "min"),
                "max_price": (price_col, "max"),
            })
        if source_col:
            agg_spec["source_types"] = (source_col, "nunique")

        coverage = comps_df.groupby("model_name").agg(**agg_spec).reset_index()

        for col in ["avg_price", "min_price", "max_price"]:
            if col not in coverage.columns:
                coverage[col] = None
        if "source_types" not in coverage.columns:
            coverage["source_types"] = None

        def coverage_band(n):
            if n >= 6:
                return "strong"
            if n >= 3:
                return "usable"
            return "thin"

        coverage["coverage_band"] = coverage["comp_count"].apply(coverage_band)
        coverage["avg_price"] = coverage["avg_price"].round(0).astype("Int64")
        coverage["min_price"] = coverage["min_price"].round(0).astype("Int64")
        coverage["max_price"] = coverage["max_price"].round(0).astype("Int64")

        st.markdown(
            coverage.to_html(index=False, classes="light-table", border=0),
            unsafe_allow_html=True
        )

        strong = int((coverage["coverage_band"] == "strong").sum())
        usable = int((coverage["coverage_band"] == "usable").sum())
        thin = int((coverage["coverage_band"] == "thin").sum())

        st.markdown('<div class="sec">What this tells us</div>', unsafe_allow_html=True)
        st.markdown(
            f"""
            - **Strong coverage:** {strong} model(s) have enough observations to support higher-confidence valuation.
            - **Usable coverage:** {usable} model(s) have enough data for a directional underwriting view.
            - **Thin coverage:** {thin} model(s) need more dealer, auction, broker, OEM-refurb or Cenotian deal data before scaling.
            """
        )

        st.caption(
            "This is portfolio-level evidence for the Oracle bet: the engine can show where underwriting confidence is strong, where it is weak, and where data acquisition should focus next."
        )
    else:
        st.warning("Could not find model_name in comparable observations.")
