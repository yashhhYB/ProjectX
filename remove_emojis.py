import re

with open("d:/projectX/app.py", "r", encoding="utf-8") as f:
    content = f.read()

# Emoji replacements
replacements = {
    "🎯": "",
    "📂": "",
    "⚖️": "",
    "⚠️": "",
    "📋": "",
    "🔄": "",
    "🏆": "",
    "📈": "",
    "🔬": "",
    "🔍": "",
    "✅": "",
    "🔴": "",
    "🟡": "",
    "❌": "",
    "⛔": "",
    "📍": "",
    "📄": "",
    "📥": "",
    "⬇️": "",
    "👆": "",
    "❤️": "",
    "🏢": "",
    "⏱️": "",
    "📅": ""
}

for emoji, replacement in replacements.items():
    content = content.replace(emoji, replacement)

# Clean up spaces left by emojis
content = content.replace("  Redrob", " Redrob").replace("###  ", "### ").replace("####  ", "#### ")
content = content.replace("###   ", "### ").replace("####   ", "#### ")
content = content.replace("<h1> Intelligent", "<h1>Intelligent")
content = content.replace("   Redrob", " Redrob")

# Enhance sidebar CSS
old_sidebar_css = """    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #f8f9fa;
        border-right: 1px solid #dadce0;
    }
    .css-1d391kg {
        background-color: #f8f9fa;
    }"""

new_sidebar_css = """    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #dadce0;
        box-shadow: 1px 0 3px 0 rgba(60,64,67,0.1);
    }
    .css-1d391kg {
        background-color: #ffffff;
    }
    
    /* Standardize sidebar text to Google style */
    section[data-testid="stSidebar"] .stMarkdown h3, 
    section[data-testid="stSidebar"] .stMarkdown h4 {
        color: #202124;
        font-weight: 500;
        letter-spacing: 0.2px;
    }
    
    section[data-testid="stSidebar"] .stRadio label,
    section[data-testid="stSidebar"] .stSlider label {
        color: #5f6368;
        font-weight: 500;
        font-size: 0.85rem;
    }"""

content = content.replace(old_sidebar_css, new_sidebar_css)

with open("d:/projectX/app.py", "w", encoding="utf-8") as f:
    f.write(content)
print("Updated app.py successfully.")
