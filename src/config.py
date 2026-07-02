"""
config.py — Central configuration for the Redrob Candidate Ranking System.
All scoring weights, thresholds, and constants live here.

v2: Rebalanced weights, expanded skill taxonomy, added career depth analysis
    constants, notice period scoring, job-hopper detection thresholds,
    production keyword lists, and certification/industry alignment sets.
"""

import os
from datetime import date, datetime

# ─────────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────────
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(
    PROJECT_ROOT,
    "[PUB] India_runs_data_and_ai_challenge",
    "India_runs_data_and_ai_challenge",
)
EMBEDDINGS_DIR = os.path.join(PROJECT_ROOT, "precompute", "embeddings")
MODEL_CACHE_DIR = os.path.join(PROJECT_ROOT, "precompute", "model_cache")

CANDIDATES_FILE = os.path.join(DATA_DIR, "candidates.jsonl")
SAMPLE_CANDIDATES_FILE = os.path.join(DATA_DIR, "sample_candidates.json")

# ─────────────────────────────────────────────────
# Embedding model
# ─────────────────────────────────────────────────
EMBEDDING_MODEL_NAME = "sentence-transformers/all-mpnet-base-v2"
EMBEDDING_DIM = 768  # Dimension of all-mpnet-base-v2 (upgraded from 384)

# ─────────────────────────────────────────────────
# Reference date for recency calculations
# ─────────────────────────────────────────────────
REFERENCE_DATE = date(2026, 6, 17)
REFERENCE_DATETIME = datetime(2026, 6, 17)

# ─────────────────────────────────────────────────
# Composite Score Weights  (must sum to 1.0)
# Rebalanced to better reflect what the JD actually values
# ─────────────────────────────────────────────────
WEIGHT_TITLE_CAREER   = 0.25   # was 0.30 — still important but less dominant
WEIGHT_SKILL_MATCH    = 0.18   # was 0.25 — quality over quantity
WEIGHT_SEMANTIC       = 0.12   # was 0.20 — support signal, not primary
WEIGHT_EXPERIENCE_FIT = 0.10   # unchanged
WEIGHT_LOCATION       = 0.05   # unchanged
WEIGHT_EDUCATION      = 0.05   # unchanged
WEIGHT_BEHAVIORAL     = 0.10   # was 0.05 — JD emphasizes behavioral signals heavily
WEIGHT_CAREER_DEPTH   = 0.08   # NEW: product vs consulting, tenure, career narrative
WEIGHT_ASSESSMENT     = 0.07   # NEW: Redrob skill_assessment_scores (free signal!)

# ─────────────────────────────────────────────────
# Experience sweet spot (Gaussian model)
# ─────────────────────────────────────────────────
EXP_IDEAL = 7.0
EXP_SIGMA = 1.5
# Legacy compat (used by prefilter)
EXP_IDEAL_MIN = 5.0
EXP_IDEAL_MAX = 9.0
EXP_ACCEPTABLE_MIN = 3.0
EXP_ACCEPTABLE_MAX = 14.0

# ─────────────────────────────────────────────────
# Title / Career scoring
# ─────────────────────────────────────────────────

# Titles that strongly signal AI/ML/Data engineering fit
STRONG_FIT_TITLES = [
    "machine learning", "ml engineer", "ai engineer", "data scientist",
    "nlp engineer", "research engineer", "deep learning", "applied scientist",
    "ranking engineer", "search engineer", "recommendation",
    "retrieval engineer", "ml ops", "mlops", "data engineer",
    "software engineer", "research scientist", "applied ml",
    "natural language processing", "information retrieval",
]

# Titles that are moderate fit (adjacent roles)
MODERATE_FIT_TITLES = [
    "backend engineer", "full stack", "platform engineer",
    "analytics engineer", "data analyst", "tech lead",
    "engineering manager", "software developer", "devops engineer",
    "site reliability", "sre",
]

# Titles that are explicit non-fit (from JD disqualifiers)
NON_FIT_TITLES = [
    "marketing", "hr", "accountant", "sales", "human resources",
    "content writer", "graphic designer", "customer support",
    "operations", "civil engineer", "mechanical engineer",
    "business analyst", "project manager", "recruiter", "product manager",
    "administrative", "representative", "coordinator",
]

# Seniority modifiers — detect seniority in title
SENIOR_TITLE_KEYWORDS = [
    "senior", "lead", "staff", "principal", "founding", "head of",
    "director", "vp", "chief",
]

# Consulting firms the JD explicitly calls out
CONSULTING_FIRMS = {
    "tcs", "wipro", "infosys", "cognizant", "accenture", "capgemini",
    "hcl", "tech mahindra", "mindtree", "mphasis", "l&t infotech",
    "hexaware", "persistent", "zensar", "ltimindtree", "cyient",
    "tata consultancy", "birlasoft", "coforge", "sonata software",
    "happiest minds", "mastek",
}

# Product companies (positive signal)
PRODUCT_COMPANY_SIGNALS = [
    "startup", "product", "saas", "platform", "fintech",
    "edtech", "healthtech", "e-commerce", "social media",
    "marketplace", "ai", "ml",
]

# ─────────────────────────────────────────────────
# Skill taxonomy — what the JD actually requires
# ─────────────────────────────────────────────────

# Target skills for Log-Weighted Duration Scorer
TARGET_SKILLS = [
    "rag", "llm", "retrieval", "vector database", "pytorch",
    "transformers", "fine-tuning", "ranking", "search engine",
    "embeddings", "information retrieval", "semantic search",
    "recommendation", "nlp", "deep learning", "machine learning",
]

# Proficiency weights
PROFICIENCY_WEIGHTS = {
    "expert": 1.0,
    "advanced": 0.8,
    "intermediate": 0.6,
    "beginner": 0.3,
}

# MUST-HAVE skills (from "Things you absolutely need")
CORE_REQUIRED_SKILLS = {
    # Embeddings & Retrieval
    "embeddings", "sentence-transformers", "sentence transformers",
    "retrieval", "information retrieval", "ir",
    "semantic search", "dense retrieval", "bge", "e5",
    "openai embeddings", "embedding",
    # Vector Databases
    "pinecone", "weaviate", "qdrant", "milvus", "faiss",
    "opensearch", "elasticsearch", "vector database", "vector db",
    "chromadb", "chroma", "vector search", "hybrid search",
    # Python
    "python",
    # NLP
    "nlp", "nlu", "natural language processing",
    "text classification", "named entity recognition", "ner",
    "transformers", "huggingface", "hugging face", "bert",
    "language models", "text mining", "text understanding",
    "spacy", "nltk", "tokenization",
    # Ranking & Search
    "ranking", "search", "recommendation", "recsys",
    "learning to rank", "l2r", "bm25",
    "ndcg", "mrr", "map", "evaluation", "a/b testing",
    "offline evaluation", "online evaluation",
    "search relevance", "query understanding",
    # ML/DL Core
    "machine learning", "deep learning", "pytorch", "tensorflow",
    "scikit-learn", "sklearn",
    "neural networks", "model training", "model deployment",
    "model serving", "inference", "mlops",
}

# NICE-TO-HAVE skills (from "Things we'd like")
NICE_TO_HAVE_SKILLS = {
    "llm fine-tuning", "fine-tuning llms", "lora", "qlora", "peft",
    "xgboost", "lightgbm", "gradient boosting",
    "distributed systems", "kubernetes", "docker",
    "spark", "ray", "dask",
    "mlflow", "weights & biases", "wandb",
    "rag", "retrieval augmented generation",
    "langchain", "llamaindex",
    "prompt engineering",
    "open source", "open-source",
    "hr tech", "recruiting", "marketplace",
    "attention mechanism", "transformer architecture",
    "data pipeline", "feature engineering", "feature store",
    "model monitoring", "drift detection",
    "aws sagemaker", "vertex ai", "azure ml",
}

# Skills that indicate WRONG domain (CV/Speech/Robotics without NLP)
WRONG_DOMAIN_SKILLS = {
    "image classification", "object detection", "computer vision",
    "image segmentation", "yolo", "opencv",
    "speech recognition", "tts", "text to speech",
    "robotics", "ros", "autonomous driving",
    "gans", "generative adversarial",
    "3d modeling", "cad", "solidworks", "ansys",
    "image processing", "video analytics",
}

# Non-technical skills (flag if these dominate)
NON_TECHNICAL_SKILLS = {
    "marketing", "seo", "content writing", "copywriting",
    "accounting", "finance", "bookkeeping",
    "project management", "six sigma", "pmp",
    "photoshop", "illustrator", "figma",
    "excel", "powerpoint", "sap",
    "sales", "crm", "salesforce",
}

# ─────────────────────────────────────────────────
# Location scoring
# ─────────────────────────────────────────────────
PREFERRED_CITIES = {
    "pune", "noida", "hyderabad", "mumbai", "delhi", "gurgaon",
    "gurugram", "new delhi", "delhi ncr", "bengaluru", "bangalore",
    "chennai",
}

INDIA_COUNTRY = {"india"}

# ─────────────────────────────────────────────────
# Behavioral signal thresholds
# ─────────────────────────────────────────────────
RECENCY_EXCELLENT_DAYS = 30
RECENCY_GOOD_DAYS = 90
RECENCY_STALE_DAYS = 180

RESPONSE_RATE_GOOD = 0.5
RESPONSE_RATE_BAD = 0.1

RESPONSE_TIME_GOOD_HOURS = 24
RESPONSE_TIME_BAD_HOURS = 168

NOTICE_PERIOD_IDEAL_DAYS = 30
NOTICE_PERIOD_MAX_DAYS = 90

PROFILE_COMPLETENESS_GOOD = 80
PROFILE_COMPLETENESS_BAD = 40

INTERVIEW_COMPLETION_GOOD = 0.7
INTERVIEW_COMPLETION_BAD = 0.3

GITHUB_ACTIVITY_GOOD = 50

# ─────────────────────────────────────────────────
# Career depth analysis constants
# ─────────────────────────────────────────────────
JOB_HOPPER_AVG_TENURE_MONTHS = 18  # JD: "switching every 1.5 years"
MIN_TENURE_STABLE = 30              # 2.5 years = stable employee signal

# Production keywords — evidence of actual shipping
PRODUCTION_KEYWORDS = {
    "deployed", "production", "scale", "scaled", "served", "built",
    "shipped", "a/b test", "a/b testing", "latency", "throughput",
    "million", "pipeline", "real-time", "real time", "infrastructure",
    "distributed", "microservice", "api", "endpoint", "monitoring",
    "load balancing", "kubernetes", "docker", "ci/cd", "cicd",
    "staging", "release", "rollout", "uptime", "sla",
    "users", "traffic", "qps", "queries per second",
    "batch processing", "streaming", "kafka", "rabbitmq",
}

# Industry alignment — tech/AI related industries
TECH_INDUSTRIES = {
    "information technology", "software", "internet", "technology",
    "artificial intelligence", "machine learning", "data analytics",
    "fintech", "edtech", "healthtech", "saas", "cloud computing",
    "e-commerce", "telecommunications", "computer software",
    "it services", "research", "deep tech",
}

# ─────────────────────────────────────────────────
# Certification scoring
# ─────────────────────────────────────────────────
RELEVANT_CERT_KEYWORDS = {
    "machine learning", "deep learning", "ai", "artificial intelligence",
    "data science", "nlp", "natural language", "tensorflow",
    "pytorch", "aws", "gcp", "azure", "cloud", "kubernetes",
    "mlops", "ml engineer", "data engineer",
}

STRONG_CERT_ISSUERS = {
    "google", "aws", "amazon", "microsoft", "nvidia",
    "deeplearning.ai", "coursera", "stanford", "mit",
    "ibm", "meta", "hugging face",
}

# ─────────────────────────────────────────────────
# Assessment scoring — Redrob skill_assessment_scores
# ─────────────────────────────────────────────────
ASSESSMENT_RELEVANT_SKILLS = {
    "machine learning", "deep learning", "nlp",
    "natural language processing", "python", "pytorch",
    "tensorflow", "data science", "ai", "artificial intelligence",
    "information retrieval", "search", "ranking",
    "neural networks", "transformers", "embeddings",
    "vector databases", "recommendation systems",
    "statistics", "mathematics", "algorithms",
    "software engineering", "system design",
}

ASSESSMENT_EXCELLENT_THRESHOLD = 80
ASSESSMENT_GOOD_THRESHOLD = 60
ASSESSMENT_POOR_THRESHOLD = 40

# ─────────────────────────────────────────────────
# Recruiter market signal thresholds
# ─────────────────────────────────────────────────
SAVED_BY_RECRUITERS_GOOD = 5
SEARCH_APPEARANCE_GOOD = 10

# ─────────────────────────────────────────────────
# Honeypot detection thresholds
# ─────────────────────────────────────────────────
HONEYPOT_MAX_EXPERT_ZERO_DURATION = 3
HONEYPOT_TITLE_DESCRIPTION_THRESHOLD = 0.15
HONEYPOT_MAX_SKILLS_EXPERT = 8

# ─────────────────────────────────────────────────
# Output
# ─────────────────────────────────────────────────
TOP_K = 100
OUTPUT_COLUMNS = ["candidate_id", "rank", "score", "reasoning"]
