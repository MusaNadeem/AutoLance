"""Cover Letter Generator Claude Prompt"""

SYSTEM_PROMPT = """You are an elite freelance proposal writer who has helped hundreds of freelancers win contracts on Upwork.

Your cover letters:
- Sound completely human and personalized — never generic AI-speak
- Open with a hook that directly addresses the client's specific pain point
- Demonstrate relevant expertise with concrete specifics (not vague claims)
- Show genuine understanding of the project requirements
- Include social proof or relevant credibility signals naturally
- Close with a clear, confident, low-pressure CTA
- Are 150-250 words — concise but compelling
- Mirror the freelancer's natural voice and tone

NEVER use: "I am writing to express", "I would love to", "I am confident", 
"As a [title]", "Please feel free", or any other corporate clichés.

Return ONLY the cover letter text — no JSON, no formatting, just the letter.
"""

def build_cover_letter_prompt(
    profile: dict,
    job: dict,
    match: dict,
    style: str = "professional",
    custom_instructions: str = "",
) -> str:
    style_guidance = {
        "professional": "Confident, polished, results-focused. Authoritative but not arrogant.",
        "casual": "Friendly, conversational, approachable. Like messaging a colleague.",
        "technical": "Lead with technical depth. Show you understand the stack and challenges.",
        "creative": "Engaging, energetic, slightly unconventional opener. Show personality.",
    }

    return f"""Write a cover letter for this job application.

FREELANCER PROFILE:
{profile}

JOB POSTING:
{job}

MATCH ANALYSIS (use these insights):
- Top strengths: {match.get('strengths', [])}
- Recommended approach: {match.get('recommended_approach', '')}
- Proposal hook: {match.get('proposal_hook', '')}
- Client quality: {match.get('client_quality_score', 'unknown')}/100

WRITING STYLE: {style}
Style guidance: {style_guidance.get(style, style_guidance['professional'])}

{f'ADDITIONAL INSTRUCTIONS: {custom_instructions}' if custom_instructions else ''}

Write the cover letter now. Start directly with the opening line."""
