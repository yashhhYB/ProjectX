# 🎯 Redrob AI — Intelligent Candidate Discovery & Ranking (v2)

> AI-powered candidate ranking system that goes beyond keyword matching to understand who actually fits the role.

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    rank.py (CLI Entry)                     │
├──────────────────────────────────────────────────────────┤
│  Stage 1: Rule-Based Pre-Filter                          │
│  → Eliminates non-technical roles (soft filtering)       │
│  → Staleness detection for behavioral down-weighting     │
├──────────────────────────────────────────────────────────┤
│  Stage 2: Semantic Scoring                               │
│  → Pre-computed all-mpnet-base-v2 embeddings (768-dim)   │
│  → Enriched candidate text (skills, certs, education)    │
│  → Cosine similarity with enriched JD embedding          │
├──────────────────────────────────────────────────────────┤
│  Stage 3: Multi-Signal Composite Scorer (9 components)   │
│  → Title/Career (25%) + Skills (18%) + Semantic (12%)   │
│  → Experience (10%) + Behavioral (10%) + Career Depth(8%)│
│  → Assessment (7%) + Location (5%) + Education (5%)      │
│  Uses ALL 23 Redrob behavioral signals                   │
├──────────────────────────────────────────────────────────┤
│  Stage 4: Enhanced Honeypot Detection                    │
│  → 9 consistency checks for impossible profiles          │
│  → Education timeline + expert skill inflation           │
├──────────────────────────────────────────────────────────┤
│  Stage 5: Unique Fact-Based Reasoning Generation         │
│  → Per-candidate explanations referencing specific facts │
│  → Rank-aware tone (enthusiastic → measured → honest)    │
│  → Optional Gemini free-tier enrichment for top 20       │
└──────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Pre-compute Embeddings (One-time, ~10-30 min)
```bash
python precompute/precompute_embeddings.py --candidates ./candidates.jsonl
```

### 3. Run Ranking (< 5 minutes, CPU, no network)
```bash
python rank.py --candidates ./candidates.jsonl --out ./submission.csv
```

### 4. Validate Submission
```bash
python validate_submission.py submission.csv
```

### 5. Launch Demo Dashboard
```bash
streamlit run app.py
```

## Scoring Methodology (v2)

| Component | Weight | What It Measures |
|-----------|--------|--------------------|
| Title & Career | 25% | Role relevance, seniority detection, career progression |
| Skill Match | 18% | Trust-weighted skill matching (proficiency × duration × endorsements) with core/nice-to-have differentiation |
| Semantic | 12% | Embedding cosine similarity (all-mpnet-base-v2) against enriched JD |
| Experience | 10% | Gaussian sweet spot centered at 7yr (σ=1.5) |
| Behavioral | 10% | ALL 23 Redrob signals: response rate, recency, notice period, GitHub, verification, market signals |
| Career Depth | 8% | Product vs consulting ratio, production keywords, career trajectory, certifications, industry alignment |
| Assessment | 7% | Redrob platform skill_assessment_scores for verified competency |
| Location | 5% | India/preferred city preference (Pune/Noida priority) |
| Education | 5% | Institution tier + field relevance + degree bonus |

### Key Design Decisions

1. **Title is the decisive signal** — A "Marketing Manager" with AI keywords is NOT a fit (the JD explicitly warns about this trap)
2. **Trust-weighted skills** — Skills are scored as `proficiency × log(duration) × log(endorsements)`, with 1.3x multiplier for core required skills
3. **All 23 behavioral signals** — Response rate, response time, recency, notice period, GitHub activity, profile completeness, verification, recruiter saves, offer acceptance, interview completion, and open-to-work status
4. **Career depth analysis** — Job-hopper detection (avg tenure < 18mo), product vs consulting ratio, production keyword density, career trajectory scoring
5. **Skill assessment integration** — Redrob's platform assessment scores are actual test results, more reliable than self-reported skills
6. **Enhanced honeypot detection** — 9 consistency checks including education timeline impossibility, excessive expert claims, and mass zero-duration experts
7. **Unique fact-based reasoning** — Each of the 100 candidates gets a substantively different reasoning string referencing their specific profile facts, strengths, and honest concerns

## Project Structure

```
├── rank.py                         # Main entry point
├── app.py                          # Streamlit demo dashboard
├── requirements.txt                # Dependencies
├── submission_metadata.yaml        # Hackathon metadata
├── src/
│   ├── config.py                   # All constants, weights, thresholds
│   ├── loader.py                   # Data loading + enriched text builder
│   ├── jd_parser.py                # JD understanding
│   ├── prefilter.py                # Soft rule-based elimination
│   ├── embeddings.py               # Semantic embedding loading
│   ├── scorer.py                   # 9-component composite scorer
│   ├── career_analyzer.py          # Career depth analysis module
│   ├── honeypot.py                 # Enhanced honeypot detection (9 checks)
│   ├── llm_reasoning.py            # Rich fact-based reasoning engine
│   └── ranker.py                   # Pipeline orchestration
├── precompute/
│   ├── precompute_embeddings.py    # One-time embedding generation
│   └── embeddings/                 # Saved .npy files
└── submission.csv                  # Final output
```

## Compute Constraints

- ✅ CPU-only (no GPU required)
- ✅ 16GB RAM (tested with 100K candidates)
- ✅ No network access during ranking
- ✅ Ranking completes in < 5 minutes
- ✅ Pre-computation is documented and separate

## Tech Stack

- **Python 3.11+**
- **sentence-transformers** (all-mpnet-base-v2) — semantic embeddings
- **FAISS** — vector similarity search
- **NumPy/Pandas** — data processing
- **Streamlit** — interactive demo dashboard
- **Plotly** — visualizations

## AI Tools Declaration

AI tools were used as development aids (not for ranking logic):
- **Claude** — architecture discussion, code review
- **Gemini** — optional reasoning enrichment (free tier, offline fallback)
- **Antigravity IDE** — development workflow

No candidate data was fed to any LLM. The ranking is fully deterministic and offline.
