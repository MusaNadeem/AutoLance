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
    tone: str = "professional",
    custom_instructions: str = "",
) -> str:
    style_guidance = {
        "professional": "Confident, polished, results-focused. Authoritative but not arrogant.",
        "casual": "Friendly, conversational, approachable. Like messaging a colleague.",
        "technical": "Lead with technical depth. Show you understand the stack and challenges.",
        "creative": "Engaging, energetic, slightly unconventional opener. Show personality.",
    }

    # Phase 3 tone overrides — replace style_guidance when tone is set explicitly
    tone_instruction_blocks = {
        "professional": (
            "TONE: Formal and results-focused. Use precise metrics language. "
            "No contractions. No casual phrasing. Lead with a quantified outcome or "
            "specific technical credential. Keep every sentence purposeful."
        ),
        "friendly": (
            "TONE: Warm, conversational, human. Use contractions freely (I've, I'm, you'll). "
            "Write as if talking to a smart colleague over coffee. "
            "Show genuine enthusiasm without being sycophantic."
        ),
        "bold": (
            "TONE: Lead immediately with your strongest value proposition — no preamble, "
            "no pleasantries. First sentence must be a direct claim or result. "
            "Be direct, brief, and confident. Aim for 120–180 words max."
        ),
    }

    # tone param takes precedence over style when it's one of the Phase 3 values
    if tone in tone_instruction_blocks:
        tone_block = tone_instruction_blocks[tone]
        effective_style_guidance = tone_instruction_blocks[tone]
    else:
        tone_block = ""
        effective_style_guidance = style_guidance.get(style, style_guidance["professional"])

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

{tone_block or f'WRITING STYLE: {style}\nStyle guidance: {effective_style_guidance}'}

{f'ADDITIONAL INSTRUCTIONS: {custom_instructions}' if custom_instructions else ''}

Write the cover letter now. Start directly with the opening line."""
