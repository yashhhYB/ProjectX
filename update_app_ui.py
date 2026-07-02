import re

with open("d:/projectX/app.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add Persona Lab to Sidebar
sidebar_marker = """    # Weight configuration"""
persona_code = """    # Live Recruiter Persona Lab
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

    # Weight configuration"""
content = content.replace(sidebar_marker, persona_code)

# 2. Update Tabs
tabs_marker = 'tab1, tab2, tab3, tab4 = st.tabs(["📊 Rankings", " Analytics", " JD Analysis", " Export"])'
tabs_replacement = 'tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Rankings", "📈 Analytics", "🔍 JD Analysis", "🛑 Honeypot Audit", "📥 Export"])'
content = content.replace(tabs_marker, tabs_replacement)
content = content.replace('tab1, tab2, tab3, tab4 = st.tabs([" Rankings", " Analytics", " JD Analysis", " Export"])', tabs_replacement)


# 3. Add Puter.js reasoning to Candidate Cards in tab1
card_end_marker = """                st.markdown(f\"\"\"
                </div>
                \"\"\", unsafe_allow_html=True)"""

puter_code = """                st.markdown(f\"\"\"
                </div>
                \"\"\", unsafe_allow_html=True)
                
                with st.expander("Generate Live Recruiter Justification"):
                    import streamlit.components.v1 as components
                    cand_name = profile.get('name', 'Candidate')
                    cand_title = profile.get('current_title', 'Unknown')
                    cand_yoe = profile.get('years_of_experience', 0)
                    skills_str = ", ".join([s.get('name', '') for s in profile.get('skills', [])][:5])
                    
                    prompt = f"Act as {persona}. Evaluate candidate: {cand_name}, Title: {cand_title}, Exp: {cand_yoe} yrs. Skills: {skills_str}. Provide exactly a 1-sentence justification for whether to interview them."
                    
                    html_code = f\"\"\"
                    <html>
                    <head>
                        <script src="https://js.puter.com/v2/"></script>
                        <style>
                            body {{ font-family: Roboto, sans-serif; color: #202124; font-size: 14px; background: #f8f9fa; padding: 12px; border-radius: 4px; border: 1px solid #dadce0; margin: 0; }}
                            .loading {{ color: #1a73e8; font-style: italic; }}
                        </style>
                    </head>
                    <body>
                        <div id="result" class="loading">Generating live justification via Puter.js (gemini-3.1-flash-lite)...</div>
                        <script>
                            puter.ai.chat(`{prompt}`, {{
                                model: 'gemini-3.1-flash-lite'
                            }}).then(response => {{
                                let text = typeof response === 'string' ? response : (response.message ? response.message.content : response.text);
                                document.getElementById('result').innerText = text;
                                document.getElementById('result').classList.remove('loading');
                            }}).catch(err => {{
                                document.getElementById('result').innerText = "Error: " + err;
                                document.getElementById('result').classList.remove('loading');
                            }});
                        </script>
                    </body>
                    </html>
                    \"\"\"
                    components.html(html_code, height=80)
"""
content = content.replace(card_end_marker, puter_code)


# 4. Add Honeypot Audit tab
export_tab_marker = "    with tab4:"
honeypot_tab_code = """    with tab4:
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

    with tab5:"""
content = content.replace(export_tab_marker, honeypot_tab_code)

# 5. Fix Analytics Charts (tab2) to include experience histogram
histogram_marker = """        st.markdown("### Component Analysis (Top 10)")"""
histogram_code = """        st.markdown("### 📊 Final Shortlist Experience Distribution")
        df = pd.DataFrame([r["candidate"]["profile"] for r in top_n])
        if "years_of_experience" in df.columns:
            fig_hist = px.histogram(
                df, x="years_of_experience", nbins=15,
                title="Years of Experience (Top Candidates)",
                color_discrete_sequence=["#1a73e8"],
                template="plotly_white"
            )
            st.plotly_chart(fig_hist, use_container_width=True)

        st.markdown("### 🔬 Component Analysis (Top 10)")"""
content = content.replace(histogram_marker, histogram_code)

with open("d:/projectX/app.py", "w", encoding="utf-8") as f:
    f.write(content)

print("app.py updated successfully.")
