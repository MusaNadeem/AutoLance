"""Cover Letter Generator Claude Prompt"""

SYSTEM_PROMPT = "You are an expert Upwork freelancer writing a winning proposal."

def build_cover_letter_prompt(
    profile: dict,
    job: dict,
    match: dict,
    style: str = "professional",
    tone: str = "professional",
    custom_instructions: str = "",
) -> str:
    # Extract variables safely from the dictionaries
    job_title = job.get('title', 'Unknown')
    job_description = job.get('description', '')
    budget = job.get('budget_type', 'Unknown')
    
    req_skills = job.get('required_skills', '')
    if isinstance(req_skills, list):
        req_skills = [s.get('name', str(s)) if isinstance(s, dict) else str(s) for s in req_skills]
    required_skills = ', '.join(req_skills) if isinstance(req_skills, list) else str(req_skills)
    
    full_name = profile.get('headline', 'Freelancer') # Will be supplemented by headline
    prof_skills = profile.get('skills', '')
    if isinstance(prof_skills, list):
        prof_skills = [s.get('name', str(s)) if isinstance(s, dict) else str(s) for s in prof_skills]
    skills = ', '.join(prof_skills) if isinstance(prof_skills, list) else str(prof_skills)
    
    experience_level = profile.get('experience_level', '')
    niche = profile.get('niche', '')
    
    prof_spec = profile.get('specializations', '')
    if isinstance(prof_spec, list):
        prof_spec = [s.get('name', str(s)) if isinstance(s, dict) else str(s) for s in prof_spec]
    summary = ', '.join(prof_spec) if isinstance(prof_spec, list) else str(prof_spec)
    
    custom_instructions_block = f"\nAdditional Instructions:\n{custom_instructions}\n" if custom_instructions else ""

    return f"""Job Title: {job_title}
Job Description: {job_description}
Budget: {budget}
Required Skills: {required_skills}

Freelancer Profile:
- Name: {full_name}
- Skills: {skills}
- Experience Level: {experience_level}
- Niche: {niche}
- Summary: {summary}
{custom_instructions_block}
Write a concise, personalized Upwork proposal (150-200 words) that:
1. Opens with a hook directly addressing the client's specific problem (NOT "I saw your job post")
2. Shows you understand exactly what they need in 1-2 sentences
3. Briefly explains why you are the right person with 1-2 specific relevant experiences
4. Ends with a clear, low-friction call to action
5. Sounds human, confident, and direct — never generic or sycophantic
6. Never starts with "I" as the first word

Return ONLY the cover letter text — no JSON, no formatting, just the letter."""
