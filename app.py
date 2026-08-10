import streamlit as st
import re
import html
from pipeline.retrieve import retrieve
from pipeline.llm      import generate

st.set_page_config(
    page_title="PolicyPal",
    page_icon="🇮🇳",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

html, body, [class*="css"], .stApp, button, input, select, textarea {
    font-family: 'Inter', sans-serif !important;
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

.stApp { background: #F5F5F0; }

/* Navbar */
.navbar {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 18px 0 18px 0;
    border-bottom: 1px solid #E4E2DB;
    margin-bottom: 24px;
}
.navbar-dot {
    width: 28px; height: 28px;
    background: #1D9E75;
    border-radius: 7px;
    display: flex; align-items: center; justify-content: center;
    color: white; font-size: 13px; font-weight: 600;
}
.navbar-name { font-size: 15px; font-weight: 600; color: #1A1A1A; }
.navbar-tag { font-size: 12px; color: #9A9891; margin-left: 4px; }

/* Left panel */
.left-panel {
    background: #FFFFFF;
    border: 1px solid #E4E2DB;
    border-radius: 14px;
    padding: 22px 18px 22px 18px;
}

.panel-title {
    font-size: 11px;
    font-weight: 600;
    color: #1D9E75;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    padding-bottom: 14px;
    border-bottom: 1px solid #F0EEE8;
    margin-bottom: 4px;
}

/* Streamlit label override */
.stSelectbox label,
.stNumberInput label,
.stTextInput label {
    font-size: 11px !important;
    font-weight: 500 !important;
    color: #8A8880 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
    font-family: 'Inter', sans-serif !important;
}

/* Input fields */
.stSelectbox > div > div,
.stNumberInput > div > div > input,
.stTextInput > div > div > input {
    background: #FAFAF8 !important;
    border: 1px solid #E4E2DB !important;
    border-radius: 8px !important;
    font-size: 13px !important;
    font-family: 'Inter', sans-serif !important;
    color: #1A1A1A !important;
}

/* Search button */
.stButton > button {
    background: #1D9E75 !important;
    color: white !important;
    border: none !important;
    border-radius: 9px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 11px 16px !important;
    width: 100% !important;
    margin-top: 4px !important;
    letter-spacing: 0.01em !important;
}
.stButton > button:hover { background: #178a65 !important; }

/* Right panel header */
.right-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;
}
.right-title {
    font-size: 16px;
    font-weight: 600;
    color: #1A1A1A;
}
.result-count {
    background: #E1F5EE;
    color: #0F6E56;
    border: 1px solid #9FE1CB;
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 11px;
    font-weight: 500;
}

/* Scheme card */
.scheme-card {
    background: #FFFFFF;
    border: 1px solid #E4E2DB;
    border-left: 3px solid #1D9E75;
    border-radius: 0 11px 11px 0;
    padding: 16px 18px;
    margin-bottom: 12px;
}
.sc-num {
    font-size: 10px;
    font-weight: 600;
    color: #1D9E75;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    margin-bottom: 4px;
}
.sc-title {
    font-size: 14px;
    font-weight: 600;
    color: #1A1A1A;
    margin-bottom: 7px;
    line-height: 1.4;
}
.sc-body {
    font-size: 12px;
    color: #6A6860;
    line-height: 1.65;
    margin-bottom: 8px;
}
.sc-link {
    font-size: 11px;
    color: #1D9E75;
    font-weight: 500;
}

/* Empty state */
.empty-right {
    background: #FFFFFF;
    border: 1px dashed #D8D6CF;
    border-radius: 14px;
    padding: 56px 24px;
    text-align: center;
}
.empty-right h3 {
    font-size: 14px;
    font-weight: 500;
    color: #4A4840;
    margin-bottom: 8px;
}
.empty-right p {
    font-size: 12px;
    color: #9A9891;
    line-height: 1.7;
}

.footer-note {
    font-size: 10px;
    color: #C0BEB8;
    text-align: center;
    margin-top: 14px;
    line-height: 1.6;
}
</style>
""", unsafe_allow_html=True)

# ── Navbar ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="navbar">
    <div class="navbar-dot">P</div>
    <span class="navbar-name">PolicyPal</span>
    <span class="navbar-tag">— Government schemes for every Indian</span>
</div>
""", unsafe_allow_html=True)

# ── Layout ─────────────────────────────────────────────────────────────────────
left, right = st.columns([1, 1.8], gap="large")

with left:
    st.markdown("**Your Profile**")

    state = st.selectbox(
        "State",
        ["central", "up", "mh", "ka", "rj", "mp", "wb", "tn", "gj", "pb"],
        format_func=lambda x: {
            "central": "Central (All India)",
            "up":      "Uttar Pradesh",
            "mh":      "Maharashtra",
            "ka":      "Karnataka",
            "rj":      "Rajasthan",
            "mp":      "Madhya Pradesh",
            "wb":      "West Bengal",
            "tn":      "Tamil Nadu",
            "gj":      "Gujarat",
            "pb":      "Punjab",
        }.get(x, x)
    )

    occupation = st.selectbox(
        "Occupation",
        ["farmer", "student", "worker", "business", "unemployed", "self-employed"],
        format_func=lambda x: {
            "farmer":        "Farmer / Agriculture",
            "student":       "Student",
            "worker":        "Daily Wage Worker",
            "business":      "Business Owner",
            "unemployed":    "Unemployed",
            "self-employed": "Self-Employed",
        }.get(x, x)
    )

    income = st.number_input(
        "Annual Income (₹)",
        min_value=0,
        max_value=2500000,
        value=120000,
        step=10000
    )

    category = st.selectbox(
        "Category",
        ["general", "sc", "st", "obc", "ews"],
        format_func=lambda x: {
            "general": "General",
            "sc":      "SC (Scheduled Caste)",
            "st":      "ST (Scheduled Tribe)",
            "obc":     "OBC",
            "ews":     "EWS",
        }.get(x, x)
    )

    gender = st.selectbox(
        "Gender",
        ["any", "male", "female"],
        format_func=lambda x: {
            "any":    "Not specified",
            "male":   "Male",
            "female": "Female"
        }.get(x, x)
    )

    query = st.text_input(
        "What are you looking for?",
        placeholder="e.g. farming subsidies, education loan..."
    )

    search = st.button("Find Schemes →")

    st.markdown('<div class="footer-note">Powered by LLaMA 3.2 · ChromaDB · myscheme.gov.in</div>', unsafe_allow_html=True)

# ── Profile dict ───────────────────────────────────────────────────────────────
profile = {
    "state":      state,
    "occupation": occupation,
    "income":     income,
    "category":   category,
    "gender":     gender,
}

# ── Right panel ────────────────────────────────────────────────────────────────
with right:
    if not search and "results" not in st.session_state:
        st.markdown("""
        <div class="empty-right">
            <h3>Fill your profile and hit "Find Schemes"</h3>
            <p>Searches 1000+ government schemes<br>and shows only what you qualify for.</p>
        </div>
        """, unsafe_allow_html=True)

    elif search:
        q = query if query else f"schemes for {occupation} in {state}"
        print(f"\n[PolicyPal] Button clicked!")
        print(f"[PolicyPal] Query: {q}")
        print(f"[PolicyPal] Profile: {profile}")
        with st.spinner("Searching..."):
            try:
                print("[PolicyPal] Running retrieval...")
                retrieved = retrieve(q, profile)
                print(f"[PolicyPal] Retrieved {len(retrieved)} chunks")
                print("[PolicyPal] Calling LLaMA 3.2 via Ollama...")
                answer    = generate(q, retrieved, profile)
                print(f"[PolicyPal] Got response ({len(answer)} chars)")
                st.session_state["results"] = answer
            except Exception as e:
                print(f"[PolicyPal] ERROR: {e}")
                st.error(f"Error: {e} — make sure Ollama is running and run_pipeline.py has been executed.")

    if "results" in st.session_state:
        answer = st.session_state["results"]
        items  = re.split(r'\n(?=\d+\.)', answer.strip())
        items  = [i for i in items if i.strip()]

        st.markdown(f"""
        <div class="right-header">
            <div class="right-title">Matching Schemes</div>
            <div class="result-count">{len(items)} found</div>
        </div>
        """, unsafe_allow_html=True)

        for i, item in enumerate(items):
            lines      = item.strip().splitlines()
            title_line = lines[0].lstrip("0123456789. ").strip()
            body_lines = "\n".join(lines[1:]).strip()

            link_match = re.search(r'(https?://\S+)', body_lines)
            link_text  = link_match.group(0) if link_match else ""

            body_clean = body_lines.replace(link_text, "").strip(" \n-:")
            body_clean = html.escape(body_clean)
            title_line = html.escape(title_line)

            st.markdown(f"""
            <div class="scheme-card">
                <div class="sc-num">Scheme {i+1}</div>
                <div class="sc-title">{title_line}</div>
                <div class="sc-body">{body_clean}</div>
                {'<div class="sc-link">' + link_text + '</div>' if link_text else ''}
            </div>
            """, unsafe_allow_html=True)