# Redrob Candidate Ranking System

> An intelligent, multi-signal candidate evaluation and ranking engine designed for AI/ML roles.

This repository contains the core logic, scoring engine, and inference pipeline for Redrob's candidate ranking system. It goes beyond simple keyword matching by evaluating candidates holistically across 9 critical dimensions, incorporating deep behavioral analytics and robust honeypot detection.

---

## 🎯 Architecture Overview

The pipeline processes candidates through five distinct stages:

1. **Rule-Based Pre-Filter** (`prefilter.py`): Softly filters clearly non-technical roles while maintaining high recall. Includes staleness detection to appropriately down-weight inactive profiles.
2. **Semantic Similarity** (`embeddings.py`): Computes cosine similarity between enriched candidate text (skills, certifications, education) and the job description using `all-mpnet-base-v2` (768-dim) sentence embeddings.
3. **Multi-Signal Composite Scorer** (`scorer.py`): The core evaluation engine that balances 9 components:
   - *Title & Career progression*
   - *Trust-weighted Skill Matching*
   - *Semantic Fit*
   - *Experience Gaussian Sweet Spot*
   - *Behavioral Signals (23 unique signals)*
   - *Career Depth Analysis*
   - *Verified Assessment Scores*
   - *Location Preferences*
   - *Educational Background*
4. **Honeypot Detection** (`honeypot.py`): Advanced fraud detection using 9 chronological and biographical consistency checks to catch automated or embellished profiles.
5. **Reasoning Generator** (`llm_reasoning.py`): Generates unique, specific, and fact-based justification strings for each top candidate, explaining exactly *why* they were ranked highly while acknowledging honest concerns.

---

## 📁 Repository Structure

```
├── rank.py                         # Main CLI entry point for the ranking pipeline
├── app.py                          # Streamlit UI dashboard for interacting with results
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Containerization configuration
├── submission_metadata.yaml        # Project metadata
├── precompute/
│   └── precompute_embeddings.py    # Offline embedding generation script
└── src/
    ├── __init__.py
    ├── config.py                   # Global constants, thresholds, and weights
    ├── loader.py                   # Data ingestion and text enrichment
    ├── prefilter.py                # Stage 1: Pre-filtering
    ├── embeddings.py               # Stage 2: Semantic scoring
    ├── scorer.py                   # Stage 3: Core composite scoring engine
    ├── career_analyzer.py          # Stage 3b: Career depth and trajectory analysis
    ├── honeypot.py                 # Stage 4: Profile authenticity checks
    ├── ranker.py                   # Pipeline orchestration
    └── llm_reasoning.py            # Stage 5: Reasoning string generation
```

---

## 🚀 Quick Start

### 1. Environment Setup

Install the required dependencies:
```bash
pip install -r requirements.txt
```

### 2. Pre-compute Embeddings (One-Time Setup)

The system relies on high-quality embeddings. Run this step once to download the `all-mpnet-base-v2` model and precompute the vector representations for all candidates.

```bash
python precompute/precompute_embeddings.py --candidates /path/to/candidates.jsonl
```

### 3. Run the Ranking Pipeline

Execute the full ranking pipeline. This runs entirely offline using the CPU and completes in under 5 minutes for 100K candidates.

```bash
python rank.py --candidates /path/to/candidates.jsonl --out submission.csv
```

### 4. Launch the Dashboard

Visualize the results and explore the scoring logic dynamically via the Streamlit interface:

```bash
streamlit run app.py
```

---

## 🧠 Key Design Principles

- **Deterministic & Offline:** The scoring engine requires zero network calls and no expensive LLM API usage during the ranking loop.
- **Anti-Gaming:** Skills are trust-weighted (Proficiency × Duration × Endorsements). Merely listing a keyword provides minimal score impact compared to verified usage.
- **Context-Aware:** Deep analysis of career history distinguishes between candidates who merely consult on ML models versus those who build, scale, and deploy them to production.
- **Fraud Prevention:** Explicit penalties are applied for impossible timelines, excessive expert claims relative to years of experience, and bot-like application behavior.

---

*Note: Data files, generated output files (CSV/XLSX), and presentations have been explicitly ignored from this repository to maintain a clean codebase environment.*
