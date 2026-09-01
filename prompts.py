from framework import FRAMEWORK_DIMENSIONS, FRAMEWORK_VERSION


def _dimensions_text() -> str:
    return "\n".join(f"{i+1}. {d}" for i, d in enumerate(FRAMEWORK_DIMENSIONS))


def source_research_prompt(company_name: str, company_url: str | None,
                           mode: str, cutoff_date: str | None) -> str:
    historical_rules = ""
    if mode == "historical":
        historical_rules = f"""
HISTORICAL BACKTEST MODE
Information cutoff date: {cutoff_date}

Strict rules:
- Evaluate the company as an investor standing on the cutoff date.
- For evidence used to assess the company, use only facts that were publicly knowable on or before {cutoff_date}.
- Prefer sources actually published on or before the cutoff date.
- If a later retrospective source is useful only to locate an older primary fact, clearly label it RETROSPECTIVE and do not use later outcome knowledge in the assessment.
- Do not mention post-cutoff outcomes, later funding rounds, later pivots, later failures/successes, IPOs, acquisitions, or later performance.
- If the publication date of a source cannot be established with reasonable confidence, label its date UNKNOWN and do not rely on it for time-sensitive claims.
"""
    else:
        historical_rules = """
LIVE DILIGENCE MODE
- Use the most recent reliable information available.
- Prefer primary sources for company-specific facts and high-quality independent sources for market/competitive context.
"""

    return f"""
You are the research-retrieval module of a human-in-the-loop early-stage investment diligence system.

Company: {company_name}
Company URL: {company_url or 'Not supplied'}
{historical_rules}

Use web search actively. Build a SOURCE MATERIAL REPORT, not an investment recommendation.

Research at least these areas when information is available:
- official company description and product.
- founders and relevant prior experience
- funding rounds, investors, announcements, and valuation only if publicly supported
- customer/problem evidence
- product/technology, technical papers, patents, white papers, or academic origins
- market size and market structure
- competitors and substitutes
- traction: customers, pilots, revenue, retention, growth, partnerships, usage
- business model and pricing
- unit economics or cost structure if available
- regulatory/legal dependencies
- major risks and unresolved questions

Source discipline:
1. Distinguish FACT from INFERENCE.
2. Never invent a fact because it sounds plausible.
3. Absence of evidence is not evidence of absence.
4. Preserve uncertainty where sources conflict.
5. For every material factual claim, cite a source.
6. End with a source register containing: title, publisher/domain, publication date if known, URL, and whether it is PRIMARY / INDEPENDENT / RETROSPECTIVE.
7. Explicitly list IMPORTANT INFORMATION NOT FOUND.

Do NOT score the company and do NOT say INVEST/PASS.
"""


def evidence_pack_prompt(company_name: str, mode: str, cutoff_date: str | None,
                         source_report: str, investor_material: str) -> str:
    cutoff_rule = (
        f"Use no evidence after {cutoff_date}. " if mode == "historical" else ""
    )

    return f"""
You are the evidence-analysis module of an early-stage diligence agent using Framework v{FRAMEWORK_VERSION}.

Company: {company_name}
Mode: {mode}
{('Cutoff date: ' + cutoff_date) if cutoff_date else ''}

AGENT-RETRIEVED SOURCE REPORT:
{source_report}

INVESTOR-SUPPLIED MATERIAL:
{investor_material or 'None supplied'}

{cutoff_rule}
Produce a structured EVIDENCE PACK across these dimensions:
{_dimensions_text()}

For EACH dimension provide:
- Factual evidence
- Supporting evidence
- Concerns / contrary evidence
- Missing information
- Key diligence questions

Rules:
- Distinguish fact from inference.
- Do not treat missing information as negative evidence.
- Do not make a final investment recommendation.
- Do not overwrite conflicts between sources; expose them.
- Keep source citations/URLs attached to factual claims wherever possible.
"""


def scorecard_prompt(company_name: str, evidence_pack: str) -> str:
    return f"""
You are the analytical-assessment module of an early-stage diligence system.

Company: {company_name}

EVIDENCE PACK:
{evidence_pack}

Assess the company on Framework v{FRAMEWORK_VERSION}:
{_dimensions_text()}

For each dimension provide:
- Score: 0-10
- Confidence in the score: 0-100%
- Concise rationale
- Strongest positive evidence
- Strongest negative/contrary evidence
- Most important missing evidence

Important:
- These are AGENT ASSESSMENTS, not objective measurements.
- Low evidence quality should reduce confidence, not automatically reduce the score.
- Do not produce an overall weighted score unless explicitly requested.
- Do not make an INVEST/PASS recommendation.
"""


def thesis_challenger_prompt(company_name: str, evidence_pack: str,
                             scorecard: str, prior_belief: str,
                             post_evidence_belief: str,
                             thesis: str) -> str:
    return f"""
You are the adversarial Thesis Challenger in a human-in-the-loop investment diligence system.

Company: {company_name}

EVIDENCE PACK:
{evidence_pack}

AGENT SCORECARD:
{scorecard}

INVESTOR PRIOR BELIEF:
{prior_belief}

INVESTOR POST-EVIDENCE BELIEF:
{post_evidence_belief}

INVESTOR THESIS:
{thesis}

Your task is NOT to decide whether this is a good investment. Challenge the investor's reasoning as strongly and fairly as possible.

Identify:
1. Hidden assumptions
2. Contrary evidence
3. Alternative interpretations
4. Evidence the investor may be overweighting
5. Evidence the investor may be underweighting
6. Missing information that could materially alter the thesis
7. Potential confirmation bias
8. Potential personal-experience / gut-feeling bias
9. Potential survivorship or narrative bias
10. Whether apparent constraints are structural or merely current implementation choices
11. Whether optionality is genuinely transferable or speculative
12. Marketplace disintermediation risk where relevant
13. The five highest-value diligence questions to answer next

Pay particular attention to retention, willingness to pay, CAC/LTV, unit economics, market depth versus geographic expansion, network effects, trust friction, product standardisation, regulatory dependencies, and repeat usage.

Do NOT give a final INVEST/PASS recommendation. The investor owns the final judgment.
"""


def memo_prompt(company_name: str, mode: str, cutoff_date: str | None,
                evidence_pack: str, scorecard: str, thesis: str,
                challenge: str, final_belief: str, final_decision: str) -> str:
    return f"""
You are a writing assistant. Draft a concise investment diligence memo that faithfully records the HUMAN investor's final judgment.

Company: {company_name}
Mode: {mode}
{('Cutoff date: ' + cutoff_date) if cutoff_date else ''}

EVIDENCE PACK:
{evidence_pack}

AGENT SCORECARD:
{scorecard}

INVESTOR THESIS:
{thesis}

THESIS CHALLENGE:
{challenge}

FINAL INVESTOR BELIEF:
{final_belief}

FINAL HUMAN DECISION / POSITION SIZE:
{final_decision}

Structure:
1. Executive view
2. Core thesis
3. Framework assessment summary
4. What changed through diligence
5. Bull case
6. Bear case
7. Unresolved questions
8. Probability/ambiguity assessment
9. Final HUMAN decision

Clearly distinguish Agent Assessment from Investor Judgment. Do not change the investor's decision.
"""
