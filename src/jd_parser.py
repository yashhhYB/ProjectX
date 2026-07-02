"""
jd_parser.py — Job description understanding and requirement extraction.

The JD is static for this hackathon, so we hardcode the extracted requirements
rather than dynamically parsing. This ensures consistent, deterministic scoring.
"""

# ─────────────────────────────────────────────────
# The full JD text for semantic embedding
# ─────────────────────────────────────────────────
JD_FULL_TEXT = """
Senior AI/ML Engineer — Ranking, Retrieval & Matching Systems

We are hiring a Senior AI/ML Engineer to own the intelligence layer of Redrob's product.
That means the ranking, retrieval, and matching systems that decide what recruiters see when
they search for candidates and what candidates see when they search for roles.

Required experience: 5-9 years, with significant applied ML/AI at product companies.

Must have production experience with:
- Embeddings-based retrieval systems (sentence-transformers, OpenAI embeddings, BGE, E5)
- Vector databases or hybrid search (Pinecone, Weaviate, Qdrant, Milvus, OpenSearch, FAISS)
- Strong Python and code quality
- Evaluation frameworks for ranking (NDCG, MRR, MAP, A/B testing)
- NLP, information retrieval, text understanding

Nice to have:
- LLM fine-tuning (LoRA, QLoRA, PEFT)
- Learning-to-rank models (XGBoost, neural)
- HR-tech or marketplace product experience
- Distributed systems, large-scale inference
- Open-source contributions in AI/ML

Key responsibilities:
- Ship v2 ranking system improving recruiter-engagement metrics
- Hybrid retrieval with embeddings and LLM-based re-ranking
- Build evaluation infrastructure (offline benchmarks, online A/B testing)
- Mentor growing engineering team (4 to 12 engineers)

Culture and values:
- Async-first, writing-heavy communication
- Ship fast, disagree openly, decide quickly
- Located in India preferred (Pune, Noida, Hyderabad, Mumbai, Delhi NCR)
- Sub-30 day notice period preferred

Disqualifiers:
- Pure research without production deployment
- Only consulting firm career (TCS, Infosys, Wipro, etc.)
- Computer vision, speech, or robotics without NLP/IR
- Title-chasers switching every 1.5 years
- Framework enthusiasts (LangChain tutorials only)
- No production code in last 18 months
"""

# ─────────────────────────────────────────────────
# Structured requirements for rule-based scoring
# ─────────────────────────────────────────────────

JD_REQUIREMENTS = {
    "role": "Senior AI/ML Engineer",
    "domain": "Ranking, Retrieval & Matching Systems",
    "company": "Redrob",
    "experience_range": (5.0, 9.0),
    "experience_acceptable": (3.0, 14.0),

    "must_have": [
        "Production embeddings-based retrieval",
        "Vector database / hybrid search experience",
        "Strong Python",
        "Ranking evaluation frameworks (NDCG, MRR, MAP)",
        "NLP / Information Retrieval",
    ],

    "nice_to_have": [
        "LLM fine-tuning (LoRA, QLoRA)",
        "Learning-to-rank models",
        "HR-tech / marketplace experience",
        "Distributed systems",
        "Open-source contributions",
    ],

    "disqualifiers": [
        "Pure research, no production",
        "Consulting-only career",
        "CV/Speech/Robotics without NLP",
        "Job-hopper (avg < 1.5 years)",
        "Framework enthusiast only",
    ],

    "location_preference": [
        "Pune", "Noida", "Hyderabad", "Mumbai", "Delhi NCR",
        "Bangalore", "Chennai",
    ],
    "country_preference": "India",
    "notice_period_ideal_days": 30,
}
