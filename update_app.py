with open("d:/projectX/app.py", "r", encoding="utf-8") as f:
    content = f.read()

# Replace CSS
old_css = """<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* Global */
    .stApp {
        font-family: 'Inter', sans-serif;
    }

    /* Hero header */
    .hero-header {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
        border-radius: 16px;
        padding: 2rem 2.5rem;
        margin-bottom: 1.5rem;
        border: 1px solid rgba(255, 255, 255, 0.08);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }
    .hero-header h1 {
        color: #fff;
        font-size: 2rem;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .hero-header p {
        color: rgba(255, 255, 255, 0.7);
        font-size: 1rem;
        margin-top: 0.5rem;
    }
    .hero-badge {
        display: inline-block;
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }

    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        border: 1px solid rgba(255, 255, 255, 0.06);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
        text-align: center;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #6366f1, #ec4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .metric-label {
        color: rgba(255, 255, 255, 0.6);
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 4px;
    }

    /* Candidate card */
    .candidate-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border: 1px solid rgba(255, 255, 255, 0.06);
        transition: all 0.3s ease;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
    }
    .candidate-card:hover {
        border-color: rgba(99, 102, 241, 0.4);
        box-shadow: 0 8px 32px rgba(99, 102, 241, 0.15);
        transform: translateY(-2px);
    }
    .candidate-rank {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 36px;
        height: 36px;
        border-radius: 10px;
        font-weight: 700;
        font-size: 0.9rem;
    }
    .rank-gold { background: linear-gradient(135deg, #f59e0b, #d97706); color: #fff; }
    .rank-silver { background: linear-gradient(135deg, #94a3b8, #64748b); color: #fff; }
    .rank-bronze { background: linear-gradient(135deg, #b45309, #92400e); color: #fff; }
    .rank-default { background: rgba(99, 102, 241, 0.2); color: #6366f1; }

    .score-bar {
        height: 6px;
        border-radius: 3px;
        background: rgba(255, 255, 255, 0.1);
        overflow: hidden;
        margin-top: 4px;
    }
    .score-bar-fill {
        height: 100%;
        border-radius: 3px;
        background: linear-gradient(90deg, #6366f1, #8b5cf6);
        transition: width 0.5s ease;
    }

    .tag {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 0.7rem;
        font-weight: 500;
        margin: 2px;
    }
    .tag-core { background: rgba(99, 102, 241, 0.2); color: #818cf8; }
    .tag-nice { background: rgba(16, 185, 129, 0.2); color: #6ee7b7; }
    .tag-other { background: rgba(255, 255, 255, 0.1); color: rgba(255, 255, 255, 0.5); }
    .tag-honeypot { background: rgba(239, 68, 68, 0.2); color: #fca5a5; }
    .tag-active { background: rgba(16, 185, 129, 0.2); color: #6ee7b7; }
    .tag-inactive { background: rgba(239, 68, 68, 0.2); color: #fca5a5; }

    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f0c29 0%, #1a1a2e 100%);
    }

    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>"""

new_css = """<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');

    /* Global */
    .stApp {
        font-family: 'Roboto', sans-serif;
        background-color: #f8f9fa;
        color: #202124;
    }

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

    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #f8f9fa;
        border-right: 1px solid #dadce0;
    }
    .css-1d391kg {
        background-color: #f8f9fa;
    }

    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>"""

content = content.replace(old_css, new_css)

old_sb = '''def score_bar_html(label, value, max_val=1.0):
    pct = min(value / max_val * 100, 100)
    return f"""
    <div style="display:flex;align-items:center;margin:4px 0;">
        <div style="width:90px;font-size:0.7rem;color:rgba(255,255,255,0.5);">{label}</div>
        <div class="score-bar" style="flex:1;">
            <div class="score-bar-fill" style="width:{pct:.0f}%;"></div>
        </div>
        <div style="width:40px;text-align:right;font-size:0.75rem;font-weight:600;color:#818cf8;">{value:.2f}</div>
    </div>
    """'''

new_sb = '''def score_bar_html(label, value, max_val=1.0):
    pct = min(value / max_val * 100, 100)
    return f"""
    <div style="display:flex;align-items:center;margin:4px 0;">
        <div style="width:90px;font-size:0.75rem;font-weight:500;color:#5f6368;">{label}</div>
        <div class="score-bar" style="flex:1;">
            <div class="score-bar-fill" style="width:{pct:.0f}%;"></div>
        </div>
        <div style="width:40px;text-align:right;font-size:0.75rem;font-weight:600;color:#1a73e8;">{value:.2f}</div>
    </div>
    """'''

content = content.replace(old_sb, new_sb)

content = content.replace('color:#fff;"', 'color:#202124;"')
content = content.replace('color:rgba(255,255,255,0.6);"', 'color:#5f6368;"')
content = content.replace('color:#818cf8;"', 'color:#1a73e8;"')
content = content.replace('color:rgba(255,255,255,0.4);"', 'color:#80868b;"')
content = content.replace('color:rgba(255,255,255,0.5);"', 'color:#5f6368;"')
content = content.replace('color:rgba(255,255,255,0.7);"', 'color:#3c4043;"')
content = content.replace('color:rgba(255,255,255,0.3);"', 'color:#80868b;"')

content = content.replace('template="plotly_dark"', 'template="plotly_white"')
content = content.replace('font=dict(family="Inter")', 'font=dict(family="Roboto", color="#202124")')
content = content.replace('color_discrete_sequence=["#6366f1"]', 'color_discrete_sequence=["#1a73e8"]')
content = content.replace('colors = ["#6366f1", "#8b5cf6", "#a78bfa", "#c4b5fd", "#818cf8", "#6d28d9", "#4f46e5"]', 'colors = ["#1a73e8", "#ea4335", "#fbbc04", "#34a853", "#4285f4", "#ff6d00", "#46bdc6"]')
content = content.replace('fillcolor="rgba(99,102,241,0.1)"', 'fillcolor="rgba(26,115,232,0.1)"')

with open("d:/projectX/app.py", "w", encoding="utf-8") as f:
    f.write(content)
print("Updated app.py")
