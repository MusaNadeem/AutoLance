"""Rate Optimizer Claude Prompt"""

SYSTEM_PROMPT = """You are a freelance pricing strategist and Upwork marketplace analyst.

Analyze market data to provide precise, actionable rate recommendations.
Be specific — give exact numbers, not ranges unless necessary.
Consider: skill rarity, client budget patterns, competition density, niche positioning.

Return ONLY valid JSON.
"""

def build_rate_optimizer_prompt(profile: dict, market_data: dict) -> str:
    return f"""Analyze this freelancer's positioning and recommend optimal pricing strategy.

FREELANCER PROFILE:
{profile}

MARKET DATA (scraped from recent jobs):
{market_data}

Return a JSON object:
{{
  "recommended_hourly_rate": 0,
  "recommended_hourly_rate_min": 0,
  "recommended_hourly_rate_max": 0,
  "fixed_project_multiplier": 1.0,
  "positioning": "budget|mid-market|premium|elite",
  "rationale": "2-3 sentence explanation",
  "competitive_edge": "What to emphasize to justify the rate",
  "niches_to_target": ["niche 1", "niche 2"],
  "niches_to_avoid": ["niche 1"],
  "market_insights": ["insight 1", "insight 2"],
  "rate_increase_potential": "none|small|moderate|significant",
  "rate_increase_actions": ["action 1", "action 2"]
}}"""
