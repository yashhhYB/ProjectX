"""
app.py — Streamlit Demo Dashboard for the Redrob AI Candidate Ranking System.

A premium, visually stunning + fully functional demo that:
  - Accepts a small candidate sample (≤100 candidates) or loads bundled data
  - Runs the full ranking pipeline end-to-end
  - Displays ranked candidates with interactive score breakdowns
  - Visualizes score distributions and component analysis
  - Provides side-by-side JD ↔ candidate comparison

Usage:
    streamlit run app.py
"""

import os
import sys
import json
import time
import tempfile

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.loader import load_candidates_jsonl, load_sample_candidates, build_candidate_text
from src.prefilter import prefilter_candidates
from src.scorer import compute_composite_score
from src.honeypot import detect_honeypot_signals
from src.jd_parser import JD_FULL_TEXT, JD_REQUIREMENTS
from src.config import (
    SAMPLE_CANDIDATES_FILE,
    TOP_K,
    WEIGHT_TITLE_CAREER, WEIGHT_SKILL_MATCH, WEIGHT_SEMANTIC,
    WEIGHT_EXPERIENCE_FIT, WEIGHT_LOCATION, WEIGHT_EDUCATION,
    WEIGHT_BEHAVIORAL,
)


# ─────────────────────────────────────────────────
# Page Configuration
# ─────────────────────────────────────────────────
st.set_page_config(
    page_title="Redrob AI Candidate Ranker",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────
# Custom CSS for premium dark theme
# ─────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');

    /* Global Custom Component Styles */

    /* Hero header */
    .hero-header {
        background-color: #ffffff;
        border-radius: 8px;
        padding: 2rem 2.5rem;
        margin-bottom: 1.5rem;
        border: 1px solid #dadce0;
        box-shadow: 0 1px 2px 0 rgba(60,64,67,0.3), 0 1px 3px 1px rgba(60,64,67,0.15);
    }
    .hero-header h1 {
        color: #202124;
        font-size: 2rem;
        font-weight: 500;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .hero-header p {
        color: #5f6368;
        font-size: 1rem;
        margin-top: 0.5rem;
    }
    .hero-badge {
        display: inline-block;
        background-color: #e8f0fe;
        color: #1a73e8;
        padding: 4px 12px;
        border-radius: 16px;
        font-size: 0.75rem;
        font-weight: 500;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        margin-bottom: 8px;
    }

    /* Metric cards */
    .metric-card {
        background-color: #ffffff;
        border-radius: 8px;
        padding: 1.2rem 1.5rem;
        border: 1px solid #dadce0;
        box-shadow: 0 1px 2px 0 rgba(60,64,67,0.3);
        text-align: center;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 400;
        color: #1a73e8;
        background: none;
        -webkit-text-fill-color: initial;
    }
    .metric-label {
        color: #5f6368;
        font-size: 0.8rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-top: 4px;
    }

    /* Candidate card */
    .candidate-card {
        background-color: #ffffff;
        border-radius: 8px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border: 1px solid #dadce0;
        transition: box-shadow 0.2s ease;
        box-shadow: 0 1px 2px 0 rgba(60,64,67,0.3);
    }
    .candidate-card:hover {
        box-shadow: 0 1px 3px 0 rgba(60,64,67,0.3), 0 4px 8px 3px rgba(60,64,67,0.15);
        border-color: #dadce0;
        transform: translateY(-2px);
    }
    .candidate-rank {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 36px;
        height: 36px;
        border-radius: 50%;
        font-weight: 500;
        font-size: 0.9rem;
    }
    .rank-gold { background-color: #fbbc04; color: #fff; }
    .rank-silver { background-color: #bdc1c6; color: #fff; }
    .rank-bronze { background-color: #e67c73; color: #fff; }
    .rank-default { background-color: #e8f0fe; color: #1a73e8; }

    .score-bar {
        height: 6px;
        border-radius: 3px;
        background-color: #f1f3f4;
        overflow: hidden;
        margin-top: 4px;
    }
    .score-bar-fill {
        height: 100%;
        border-radius: 3px;
        background-color: #1a73e8;
        transition: width 0.5s ease;
    }

    .tag {
        display: inline-block;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 500;
        margin: 2px;
        border: 1px solid transparent;
    }
    .tag-core { background-color: #e8f0fe; color: #1a73e8; border-color: #d2e3fc; }
    .tag-nice { background-color: #e6f4ea; color: #137333; border-color: #ceead6; }
    .tag-other { background-color: #f1f3f4; color: #5f6368; border-color: #dadce0; }
    .tag-honeypot { background-color: #fce8e6; color: #c5221f; border-color: #fad2cf; }
    .tag-active { background-color: #e6f4ea; color: #137333; border-color: #ceead6; }
    .tag-inactive { background-color: #fce8e6; color: #c5221f; border-color: #fad2cf; }

    /* Streamlit components inherit from config.toml */

    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────────

def get_rank_class(rank):
    if rank == 1: return "rank-gold"
    elif rank == 2: return "rank-silver"
    elif rank == 3: return "rank-bronze"
    return "rank-default"


def score_bar_html(label, value, max_val=1.0):
    pct = min(value / max_val * 100, 100)
    return f"""
    <div style="display:flex;align-items:center;margin:4px 0;">
        <div style="width:90px;font-size:0.75rem;font-weight:500;color:#5f6368;">{label}</div>
        <div class="score-bar" style="flex:1;">
            <div class="score-bar-fill" style="width:{pct:.0f}%;"></div>
        </div>
        <div style="width:40px;text-align:right;font-size:0.75rem;font-weight:600;color:#1a73e8;">{value:.2f}</div>
    </div>
    """


def categorize_skill(skill_name):
    from src.config import CORE_REQUIRED_SKILLS, NICE_TO_HAVE_SKILLS
    name_lower = skill_name.lower()
    if any(kw in name_lower or name_lower in kw for kw in CORE_REQUIRED_SKILLS):
        return "core"
    elif any(kw in name_lower or name_lower in kw for kw in NICE_TO_HAVE_SKILLS):
        return "nice"
    return "other"


@st.cache_resource
def get_embedding_model():
    from sentence_transformers import SentenceTransformer
    from src.config import EMBEDDING_MODEL_NAME, MODEL_CACHE_DIR
    return SentenceTransformer(EMBEDDING_MODEL_NAME, cache_folder=MODEL_CACHE_DIR)

@st.cache_data
def run_pipeline(candidates_data):
    """Run the ranking pipeline on candidate data (cached)."""
    # ── Try to compute semantic dynamically for small sets ──
    semantic_scores = {}
    if len(candidates_data) <= 500:
        try:
            model = get_embedding_model()
            from src.loader import build_candidate_text
            cand_texts = [build_candidate_text(c) for c in candidates_data]
            cand_embs = model.encode(cand_texts, normalize_embeddings=True)
            
            from src.jd_parser import JD_FULL_TEXT
            enriched_jd = f"{JD_FULL_TEXT} RAG embeddings retrieval ranking LLM fine-tuning vector database indexing search systems PyTorch pipeline"
            jd_emb = model.encode([enriched_jd], normalize_embeddings=True)
            
            from src.embeddings import compute_semantic_scores
            scores_array = compute_semantic_scores(cand_embs, jd_emb)
            
            for i, c in enumerate(candidates_data):
                cid = c.get("candidate_id", str(i))
                semantic_scores[cid] = float(scores_array[i])
        except Exception as e:
            st.warning(f"Semantic scoring fallback: {e}")
    else:
        # For large uploads, rely on precomputed
        try:
            from src.embeddings import load_precomputed_embeddings, get_semantic_score_map
            cand_embs, jd_emb, ids = load_precomputed_embeddings()
            semantic_scores = get_semantic_score_map(cand_embs, jd_emb, ids)
        except Exception:
            pass

    results = []
    for i, candidate in enumerate(candidates_data):
        cid = candidate.get("candidate_id", str(i))
        sem_score = semantic_scores.get(cid, 0.0)
        
        scores = compute_composite_score(candidate, semantic_score=sem_score)
        is_hp, hp_reasons = detect_honeypot_signals(candidate)
        if is_hp:
            scores["composite"] *= 0.01
        scores["honeypot"] = is_hp
        scores["honeypot_reasons"] = hp_reasons
        results.append({"candidate": candidate, "scores": scores})

    results.sort(key=lambda x: x["scores"]["composite"], reverse=True)
    return results


# ─────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Redrob AI Ranker")
    st.markdown("---")

    # Data source selection
    st.markdown("#### Data Source")
    data_source = st.radio(
        "Choose input:",
        ["Sample Data (50 candidates)", "Upload JSONL"],
        label_visibility="collapsed",
    )

    uploaded_file = None
    if data_source == "Upload JSONL":
        uploaded_file = st.file_uploader(
            "Upload candidates.jsonl",
            type=["jsonl", "json"],
        )

    st.markdown("---")

    # Live Recruiter Persona Lab
    st.markdown("#### Live Recruiter Persona Lab")
    persona = st.selectbox(
        "Select Persona for LLM",
        [
            "Corporate Talent Recruiter: Focuses strictly on years of experience, regional hubs, and technical degrees.",
            "Fast-paced Startup Founder: Values scrappy product-building, high eagerness metrics, and rapid project delivery.",
            "Skeptical Software Lead: Highly critical of keyword stuffers; focuses on system scalability and backend history."
        ],
        label_visibility="collapsed"
    )
    st.markdown("---")

    # Weight configuration
    st.markdown("#### Scoring Weights")
    w_title = st.slider("Title & Career", 0.0, 1.0, WEIGHT_TITLE_CAREER, 0.05)
    w_skill = st.slider("Skill Match", 0.0, 1.0, WEIGHT_SKILL_MATCH, 0.05)
    w_semantic = st.slider("Semantic Sim", 0.0, 1.0, WEIGHT_SEMANTIC, 0.05)
    w_exp = st.slider("Experience Fit", 0.0, 1.0, WEIGHT_EXPERIENCE_FIT, 0.05)
    w_loc = st.slider("Location", 0.0, 1.0, WEIGHT_LOCATION, 0.05)
    w_edu = st.slider("Education", 0.0, 1.0, WEIGHT_EDUCATION, 0.05)
    w_behav = st.slider("Behavioral", 0.0, 1.0, WEIGHT_BEHAVIORAL, 0.05)

    total_w = w_title + w_skill + w_semantic + w_exp + w_loc + w_edu + w_behav
    if abs(total_w - 1.0) > 0.01:
        st.warning(f" Weights sum to {total_w:.2f} (should be 1.0)")

    st.markdown("---")
    st.markdown("#### JD Summary")
    st.markdown(f"**Role:** {JD_REQUIREMENTS['role']}")
    st.markdown(f"**Domain:** {JD_REQUIREMENTS['domain']}")
    st.markdown(f"**Exp Range:** {JD_REQUIREMENTS['experience_range'][0]}-{JD_REQUIREMENTS['experience_range'][1]} years")
    st.markdown(f"**Location:** {', '.join(JD_REQUIREMENTS['location_preference'][:3])}...")


# ─────────────────────────────────────────────────
# Main Content
# ─────────────────────────────────────────────────

# Hero Header
st.markdown("""
<div class="hero-header">
    <span class="hero-badge">Redrob Hackathon 2026</span>
    <h1>Intelligent Candidate Discovery & Ranking</h1>
    <p>AI-powered candidate ranking that understands who actually fits — not just keyword matching.</p>
</div>
""", unsafe_allow_html=True)

# Load data
candidates = None
if data_source == "Sample Data (50 candidates)":
    if os.path.exists(SAMPLE_CANDIDATES_FILE):
        candidates = load_sample_candidates(SAMPLE_CANDIDATES_FILE)
    else:
        st.error("Sample candidates file not found. Please check the data path.")
elif uploaded_file is not None:
    content = uploaded_file.read().decode("utf-8")
    if uploaded_file.name.endswith(".json"):
        candidates = json.loads(content)
    else:
        candidates = [json.loads(line) for line in content.strip().split("\n") if line.strip()]

if candidates:
    # Run pipeline
    with st.spinner(" Running ranking pipeline..."):
        start = time.time()
        results = run_pipeline(candidates)
        elapsed = time.time() - start

    # ── Metrics Row ──
    total = len(results)
    hp_count = sum(1 for r in results if r["scores"].get("honeypot", False))
    top_score = results[0]["scores"]["composite"] if results else 0
    avg_score = sum(r["scores"]["composite"] for r in results) / total if total else 0

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total}</div>
            <div class="metric-label">Candidates Scored</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{top_score:.3f}</div>
            <div class="metric-label">Top Score</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{avg_score:.3f}</div>
            <div class="metric-label">Average Score</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{hp_count}</div>
            <div class="metric-label">Honeypots Found</div>
        </div>
        """, unsafe_allow_html=True)
    with col5:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{elapsed:.1f}s</div>
            <div class="metric-label">Pipeline Time</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Tabs ──
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Rankings", "📈 Analytics", "🔍 JD Analysis", "🛑 Honeypot Audit", "📥 Export"])

    with tab1:
        # Ranked candidate cards
        st.markdown("### Ranked Candidates")

        # Top N selector
        show_n = st.slider("Show top N candidates:", 5, min(100, total), min(20, total))

        for rank_idx, entry in enumerate(results[:show_n], start=1):
            candidate = entry["candidate"]
            scores = entry["scores"]
            profile = candidate.get("profile", {})
            signals = candidate.get("redrob_signals", {})
            is_hp = scores.get("honeypot", False)

            rank_class = get_rank_class(rank_idx)

            # Build skill tags
            skill_tags = ""
            for s in candidate.get("skills", [])[:8]:
                cat = categorize_skill(s.get("name", ""))
                tag_class = f"tag-{cat}"
                skill_tags += f'<span class="tag {tag_class}">{s.get("name", "")}</span>'

            # Status tags
            status_tags = ""
            if signals.get("open_to_work_flag"):
                status_tags += '<span class="tag tag-active">Open to Work</span>'
            if is_hp:
                status_tags += '<span class="tag tag-honeypot"> Honeypot</span>'

            last_active = signals.get("last_active_date", "N/A")

            with st.container():
                c1, c2 = st.columns([3, 2])

                with c1:
                    st.markdown(f"""
                    <div class="candidate-card">
                        <div style="display:flex;align-items:center;gap:12px;margin-bottom:10px;">
                            <div class="candidate-rank {rank_class}">#{rank_idx}</div>
                            <div>
                                <div style="font-weight:700;font-size:1.1rem;color:#202124;">
                                    {profile.get('anonymized_name', 'N/A')}
                                </div>
                                <div style="font-size:0.85rem;color:#5f6368;">
                                    {profile.get('headline', '')}
                                </div>
                            </div>
                            <div style="margin-left:auto;text-align:right;">
                                <div style="font-size:1.3rem;font-weight:700;color:#1a73e8;">
                                    {scores['composite']:.4f}
                                </div>
                                <div style="font-size:0.7rem;color:#80868b;">composite score</div>
                            </div>
                        </div>
                        <div style="font-size:0.8rem;color:rgba(255,255,255,0.5);margin-bottom:8px;">
                             {profile.get('location', 'N/A')}, {profile.get('country', 'N/A')} •
                             {profile.get('current_company', 'N/A')} •
                             {profile.get('years_of_experience', 0):.1f}yr exp •
                             Last active: {last_active}
                        </div>
                        <div style="margin-bottom:8px;">{status_tags}</div>
                        <div style="margin-bottom:8px;">{skill_tags}</div>
                    </div>
                    """, unsafe_allow_html=True)

                with c2:
                    st.markdown(f"""
                    <div class="candidate-card" style="padding:1rem;">
                        <div style="font-size:0.8rem;font-weight:600;color:rgba(255,255,255,0.7);margin-bottom:8px;">Score Breakdown</div>
                        {score_bar_html("Title/Career", scores.get('title_career', 0))}
                        {score_bar_html("Skills", scores.get('skill_match', 0))}
                        {score_bar_html("Semantic", scores.get('semantic', 0))}
                        {score_bar_html("Experience", scores.get('experience_fit', 0))}
                        {score_bar_html("Location", scores.get('location', 0))}
                        {score_bar_html("Education", scores.get('education', 0))}
                        {score_bar_html("Behavioral", scores.get('behavioral', 0))}
                    </div>
                    """, unsafe_allow_html=True)

    with tab2:
        st.markdown("### Score Distribution & Analytics")

        # Score distribution
        all_scores = [r["scores"]["composite"] for r in results]
        fig_dist = px.histogram(
            x=all_scores,
            nbins=30,
            title="Composite Score Distribution",
            labels={"x": "Score", "y": "Count"},
            color_discrete_sequence=["#1a73e8"],
        )
        fig_dist.update_layout(
            template="plotly_white",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Roboto", color="#202124"),
        )
        st.plotly_chart(fig_dist, width='stretch')

        # Component comparison for top 10
        st.markdown("### 📊 Final Shortlist Experience Distribution")
        df = pd.DataFrame([r["candidate"]["profile"] for r in results])
        if "years_of_experience" in df.columns:
            fig_hist = px.histogram(
                df, x="years_of_experience", nbins=15,
                title="Years of Experience (Top Candidates)",
                color_discrete_sequence=["#1a73e8"],
                template="plotly_white"
            )
            st.plotly_chart(fig_hist, width='stretch')

        st.markdown("### 🔬 Component Analysis (Top 10)")
        top_10_data = []
        for i, entry in enumerate(results[:10], 1):
            profile = entry["candidate"].get("profile", {})
            s = entry["scores"]
            top_10_data.append({
                "Candidate": f"#{i} {profile.get('anonymized_name', 'N/A')[:15]}",
                "Title/Career": s.get("title_career", 0),
                "Skills": s.get("skill_match", 0),
                "Semantic": s.get("semantic", 0),
                "Experience": s.get("experience_fit", 0),
                "Location": s.get("location", 0),
                "Education": s.get("education", 0),
                "Behavioral": s.get("behavioral", 0),
            })

        df_top10 = pd.DataFrame(top_10_data)
        fig_radar = go.Figure()

        components = ["Title/Career", "Skills", "Semantic", "Experience", "Location", "Education", "Behavioral"]
        colors = ["#1a73e8", "#ea4335", "#fbbc04", "#34a853", "#4285f4", "#ff6d00", "#46bdc6"]

        for i, row in df_top10.head(5).iterrows():
            vals = [row[c] for c in components]
            vals.append(vals[0])  # Close the polygon
            fig_radar.add_trace(go.Scatterpolar(
                r=vals,
                theta=components + [components[0]],
                fill='toself',
                name=row["Candidate"],
                opacity=0.6,
            ))

        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
            template="plotly_white",
            paper_bgcolor="rgba(0,0,0,0)",
            title="Component Radar — Top 5 Candidates",
            font=dict(family="Roboto", color="#202124"),
        )
        st.plotly_chart(fig_radar, width='stretch')

        # Experience distribution
        yoe_data = [
            {
                "YoE": entry["candidate"].get("profile", {}).get("years_of_experience", 0),
                "Score": entry["scores"]["composite"],
                "Name": entry["candidate"].get("profile", {}).get("anonymized_name", ""),
            }
            for entry in results[:50]
        ]
        fig_yoe = px.scatter(
            pd.DataFrame(yoe_data),
            x="YoE", y="Score",
            hover_data=["Name"],
            title="Experience vs Score (Top 50)",
            color="Score",
            color_continuous_scale="Viridis",
        )
        fig_yoe.update_layout(
            template="plotly_white",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Roboto", color="#202124"),
        )
        # Add sweet spot band
        fig_yoe.add_vrect(x0=5, x1=9, fillcolor="rgba(26,115,232,0.1)",
                          line_width=0, annotation_text="Sweet Spot (5-9yr)")
        st.plotly_chart(fig_yoe, width='stretch')

    with tab3:
        st.markdown("### Job Description Analysis")
        st.markdown("---")

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("#### Must-Have Requirements")
            for req in JD_REQUIREMENTS["must_have"]:
                st.markdown(f"-  {req}")

            st.markdown("#### Nice-to-Have")
            for req in JD_REQUIREMENTS["nice_to_have"]:
                st.markdown(f"-  {req}")

        with col_b:
            st.markdown("#### Disqualifiers")
            for dis in JD_REQUIREMENTS["disqualifiers"]:
                st.markdown(f"-  {dis}")

            st.markdown("#### Location Preference")
            st.markdown(", ".join(JD_REQUIREMENTS["location_preference"]))

        st.markdown("---")
        with st.expander(" Full Job Description Text"):
            st.text(JD_FULL_TEXT)

    with tab4:
        st.markdown("### 🛑 Honeypot Audit Inspector")
        honeypots = [r for r in results if r["scores"].get("honeypot", False)]
        
        if not honeypots:
            st.success("No honeypots detected in this dataset!")
        else:
            st.error(f"Detected {len(honeypots)} fraudulent or impossible profiles.")
            for i, hp in enumerate(honeypots):
                cand = hp["candidate"]
                reasons = hp["scores"].get("honeypot_reasons", [])
                name = cand.get("profile", {}).get("name", f"Candidate {i+1}")
                title = cand.get("profile", {}).get("current_title", "Unknown")
                
                with st.container():
                    st.markdown(f"**{name}** — {title}")
                    for r in reasons:
                        st.markdown(f"- ⛔ `{r}`")
                    st.markdown("---")

    with tab5:
        st.markdown("### Export Results")

        # Build CSV data
        csv_data = []
        for rank_idx, entry in enumerate(results[:100], start=1):
            candidate = entry["candidate"]
            profile = candidate.get("profile", {})
            scores = entry["scores"]

            # Build reasoning
            title = profile.get("current_title", "Unknown")
            company = profile.get("current_company", "Unknown")
            yoe = profile.get("years_of_experience", 0)

            skills_list = [s.get("name", "") for s in candidate.get("skills", [])[:5]]
            reasoning = (
                f"{title} at {company} ({yoe:.1f}yr); "
                f"skills: {', '.join(skills_list[:3])}; "
                f"title_score={scores.get('title_career', 0):.2f}"
            )

            csv_data.append({
                "candidate_id": candidate.get("candidate_id"),
                "rank": rank_idx,
                "score": round(scores["composite"], 4),
                "reasoning": reasoning,
            })

        df_export = pd.DataFrame(csv_data)
        st.dataframe(df_export, width='stretch', height=400)

        csv_string = df_export.to_csv(index=False)
        st.download_button(
            " Download submission.csv",
            csv_string,
            "submission.csv",
            "text/csv",
            width='stretch',
        )

else:
    st.info(" Select a data source from the sidebar to begin ranking candidates.")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align:center;color:rgba(255,255,255,0.3);font-size:0.75rem;'>"
    "Built with  for the Redrob AI Hackathon 2026 | Powered by sentence-transformers + FAISS"
    "</div>",
    unsafe_allow_html=True,
)
