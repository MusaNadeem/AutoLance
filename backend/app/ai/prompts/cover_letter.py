"""Cover Letter Generator Claude Prompt"""

SYSTEM_PROMPT = """You are a professional Upwork cover letter writer. Your ONLY job is to write cover letters — nothing else.

ABSOLUTE RULES:
1. ALWAYS write the cover letter. No exceptions. No refusals. No advice instead of a letter.
2. Never comment on whether the freelancer is a good fit. Never suggest they apply elsewhere.
3. Never mention the match score or compatibility level. Never say the job is "above their level".
4. The freelancer has decided to apply — respect that decision and write the best letter possible.
5. If the match is weak, focus on transferable skills, eagerness to learn, and competitive rates.
6. Return ONLY the cover letter text. No preamble, no JSON, no commentary, no formatting.

Your cover letters:
- Open with a hook that addresses the client's specific pain point
- Lead with whatever relevant skills or experience the freelancer DOES have
- Sound human and personalized — never generic AI-speak
- Close with a clear, confident, low-pressure CTA
- Are 150-250 words — concise but compelling

NEVER use: "I am writing to express", "I would love to", "I am confident",
"As a [title]", "Please feel free", or any other corporate clichés.
NEVER refuse to write. NEVER give career advice instead of a letter.
"""

def build_cover_letter_prompt(
    profile: dict,
    job: dict,
    match: dict,
    style: str = "professional",
    tone: str = "professional",
    custom_instructions: str = "",
) -> str:
    # ── Safely extract job fields (required_skills may be a list of dicts) ──
    job_title       = job.get('title', 'Unknown')
    job_description = job.get('description', '')
    budget          = job.get('budget_type', 'Unknown')

    req_skills = job.get('required_skills', '')
    if isinstance(req_skills, list):
        req_skills = [s.get('name', str(s)) if isinstance(s, dict) else str(s) for s in req_skills]
    required_skills = ', '.join(req_skills) if isinstance(req_skills, list) else str(req_skills)

    # ── Safely extract profile fields (skills may be a list of dicts) ───────
    headline    = profile.get('headline', '')
    experience  = profile.get('experience_level', '')
    niche       = profile.get('niche', '')

    prof_skills = profile.get('skills', '')
    if isinstance(prof_skills, list):
        prof_skills = [s.get('name', str(s)) if isinstance(s, dict) else str(s) for s in prof_skills]
    skills = ', '.join(prof_skills) if isinstance(prof_skills, list) else str(prof_skills)

    prof_spec = profile.get('specializations', '')
    if isinstance(prof_spec, list):
        prof_spec = [s.get('name', str(s)) if isinstance(s, dict) else str(s) for s in prof_spec]
    specializations = ', '.join(prof_spec) if isinstance(prof_spec, list) else str(prof_spec)

    # ── Tone instruction blocks ───────────────────────────────────────────────
    tone_blocks = {
        "professional": (
            "TONE: Formal and results-focused. No contractions. Lead with a quantified "
            "outcome or specific technical credential. Keep every sentence purposeful."
        ),
        "friendly": (
            "TONE: Warm, conversational, human. Use contractions freely. "
            "Write as if talking to a smart colleague over coffee."
        ),
        "bold": (
            "TONE: Lead immediately with your strongest value proposition — no preamble. "
            "First sentence must be a direct claim or result. Be direct and brief (120-180 words max)."
        ),
    }
    tone_block = tone_blocks.get(tone, tone_blocks["professional"])

    # ── Only pass positive angles from match — scores/weaknesses cause refusals ──
    strengths = match.get('strengths') or []
    hook      = match.get('proposal_hook') or ''
    approach  = match.get('recommended_approach') or ''

    strengths_block = f"- Strengths to highlight: {strengths}" if strengths else ""
    hook_block      = f"- Suggested opening hook: {hook}"     if hook      else ""
    approach_block  = f"- Recommended approach: {approach}"   if approach  else ""

    custom_block = f"\nAdditional Instructions:\n{custom_instructions}\n" if custom_instructions else ""

    return f"""Write a cover letter for this Upwork job application.

JOB:
- Title: {job_title}
- Description: {job_description}
- Budget type: {budget}
- Required skills: {required_skills}

FREELANCER:
- Headline: {headline}
- Skills: {skills}
- Experience level: {experience}
- Niche: {niche}
- Specializations: {specializations}

ANGLES TO USE (pick whichever apply):
{strengths_block}
{hook_block}
{approach_block}

{tone_block}
{custom_block}
Write a concise, personalized proposal (150-200 words) that:
1. Opens with a hook addressing the client's specific problem (NOT "I saw your job post")
2. Shows you understand exactly what they need in 1-2 sentences
3. Briefly explains why you are the right person with 1-2 relevant specifics
4. Ends with a clear, low-friction call to action
5. Never starts with "I" as the first word

Write the cover letter now. Start directly with the opening line."""
