"""CV Parser Claude Prompt"""

SYSTEM_PROMPT = """You are an expert resume analyst and freelancer profiling specialist with 15+ years of experience in talent assessment.

Your task is to analyze resumes and extract comprehensive structured data.

Rules:
- Be precise and analytical, not generous
- Infer experience level from years of experience and project complexity
- Detect the primary niche even if not explicitly stated
- Rate inference confidently based on market data
- Return ONLY valid JSON — no markdown, no prose, no explanations outside the JSON
"""

def build_cv_parser_prompt(resume_text: str) -> str:
    return f"""Analyze this resume and return a JSON object with exactly this structure:

{{
  "headline": "Professional one-line summary (max 100 chars)",
  "summary": "2-3 sentence professional summary",
  "skills": [
    {{"name": "skill name", "level": "beginner|intermediate|advanced|expert", "years": 0}}
  ],
  "experience_level": "junior|mid|senior|expert",
  "niche": "Primary professional niche (e.g., 'React Frontend Developer', 'Python Data Engineer')",
  "specializations": ["specialization 1", "specialization 2"],
  "communication_tone": "formal|casual|technical",
  "inferred_hourly_rate_min": 0,
  "inferred_hourly_rate_max": 0,
  "preferred_project_types": ["fixed", "hourly", "long-term"],
  "preferred_industries": ["industry 1", "industry 2"],
  "years_total_experience": 0,
  "education": [
    {{"degree": "...", "field": "...", "institution": "...", "year": 0}}
  ],
  "certifications": ["cert 1", "cert 2"],
  "languages": [
    {{"language": "...", "level": "native|fluent|professional|basic"}}
  ]
}}

RESUME TEXT:
{resume_text}"""
