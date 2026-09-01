import json
from datetime import datetime
from pathlib import Path
import re
from framework import FRAMEWORK_VERSION
from io_utils import collect_investor_material
from llm import call_llm
from models import BeliefSnapshot, CompanyContext, ProbabilityRange
from prompts import (
    evidence_pack_prompt,
    memo_prompt,
    scorecard_prompt,
    source_research_prompt,
    thesis_challenger_prompt,
)

BASE_OUTPUT_DIR = Path("outputs")
BASE_OUTPUT_DIR.mkdir(exist_ok=True)


def slugify_company_name(company_name: str) -> str:
    """
    Convert a company name into a safe folder name.

    Examples:
        "Gigged.AI" -> "gigged_ai"
        "TileBio Ltd" -> "tilebio_ltd"
        "A&B Technologies" -> "a_b_technologies"
    """
    slug = company_name.lower().strip()

    # Replace non-alphanumeric characters with underscores
    slug = re.sub(r"[^a-z0-9]+", "_", slug)

    # Remove leading/trailing underscores
    slug = slug.strip("_")

    return slug



def ask_float(prompt: str) -> float:
    while True:
        try:
            value = float(input(prompt).strip())
            if 0 <= value <= 100:
                return value
            print("Enter a number from 0 to 100.")
        except ValueError:
            print("Enter a valid number.")


def ask_probability_range(label: str) -> ProbabilityRange:
    print(f"\n{label}")
    while True:
        p = ProbabilityRange(
            lower=ask_float("  Lower plausible probability (%): "),
            best=ask_float("  Best estimate (%): "),
            upper=ask_float("  Upper plausible probability (%): "),
        )
        try:
            p.validate()
            return p
        except ValueError as exc:
            print(f"Invalid range: {exc}. Please enter it again.")


def ask_belief_snapshot(stage_name: str) -> BeliefSnapshot:
    print(f"\n=== {stage_name} ===")
    snapshot = BeliefSnapshot(
        survival_3y=ask_probability_range(
            "P(survive at least 3 years)"
        ),
        sustainable_given_survival=ask_probability_range(
            "P(build a sustainable business | survives 3 years)"
        ),
        notes=input("\nBrief reasoning / intuition: ").strip(),
    )
    snapshot.validate()
    show_belief(snapshot)
    return snapshot


def belief_as_text(snapshot: BeliefSnapshot) -> str:
    s = snapshot.survival_3y
    b = snapshot.sustainable_given_survival
    return f"""
P(survive 3 years): lower={s.lower:.1f}%, best={s.best:.1f}%, upper={s.upper:.1f}%
Ambiguity width (survival): {s.ambiguity_width:.1f} percentage points
P(sustainable business | survive): lower={b.lower:.1f}%, best={b.best:.1f}%, upper={b.upper:.1f}%
Ambiguity width (sustainable | survive): {b.ambiguity_width:.1f} percentage points
Implied best-estimate P(sustainable business): {snapshot.implied_sustainable_business_best():.1f}%
Reasoning: {snapshot.notes}
""".strip()


def show_belief(snapshot: BeliefSnapshot) -> None:
    print("\n" + belief_as_text(snapshot))


def get_company_context() -> CompanyContext:
    print(f"\n=== EARLY-STAGE DILIGENCE AGENT — Framework v{FRAMEWORK_VERSION} ===\n")
    name = input("Company name: ").strip()
    url = input("Company URL (optional): ").strip() or None

    print("\nMode:")
    print("  1) Live diligence")
    print("  2) Historical backtest")
    choice = input("Select 1 or 2: ").strip()

    if choice == "2":
        while True:
            cutoff = input("Information cutoff date (YYYY-MM-DD): ").strip()
            try:
                datetime.strptime(cutoff, "%Y-%m-%d")
                break
            except ValueError:
                print("Use YYYY-MM-DD, e.g. 2008-12-01.")
        return CompanyContext(name=name, url=url, mode="historical", cutoff_date=cutoff)

    return CompanyContext(name=name, url=url, mode="live", cutoff_date=None)


def save_text(output_dir: Path, prefix: str, content: str) -> Path:
    path = output_dir / f"{prefix}.md"
    path.write_text(content, encoding="utf-8")
    return path


def save_json(output_dir: Path, payload: dict) -> Path:
    path = output_dir / "session.json"
    path.write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8"
    )
    return path


def print_section(title: str, content: str) -> None:
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72 + "\n")
    print(content)


def main():
    ctx = get_company_context()

    company = ctx.name
    url = ctx.url

    company_slug = slugify_company_name(company)

    output_dir = BASE_OUTPUT_DIR / company_slug
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nOutput folder: {output_dir}")

    # p1: true human prior, before the agent presents detailed evidence.
    prior = ask_belief_snapshot("INVESTOR PRIOR — BEFORE EVIDENCE PACK (p1)")

    print("\nAgent is researching the company and sourcing material from the web...")
    research_prompt = source_research_prompt(
        ctx.name, ctx.url, ctx.mode, ctx.cutoff_date
    )
    source_report = call_llm(
        research_prompt,
        use_web=True,
        reasoning_effort="medium",
    )
    print_section("AGENT-RETRIEVED SOURCE MATERIAL", source_report)
    save_text("sources", ctx.name, source_report)

    investor_material = collect_investor_material()

    print("\nBuilding Evidence Pack from agent + investor material...")
    ep_prompt = evidence_pack_prompt(
        ctx.name,
        ctx.mode,
        ctx.cutoff_date,
        source_report,
        investor_material,
    )
    evidence_pack = call_llm(ep_prompt, reasoning_effort="medium")
    print_section("EVIDENCE PACK", evidence_pack)
    save_text("evidence_pack", ctx.name, evidence_pack)

    # p2: human belief after seeing evidence.
    post_ep = ask_belief_snapshot("INVESTOR BELIEF — AFTER EVIDENCE PACK (p2)")

    print("\nGenerating Agent Assessment across the 10 dimensions...")
    scorecard = call_llm(
        scorecard_prompt(ctx.name, evidence_pack),
        reasoning_effort="medium",
    )
    print_section("AGENT 10-DIMENSION ASSESSMENT", scorecard)
    save_text("scorecard", ctx.name, scorecard)

    print("\n=== INVESTOR THESIS ===")
    print("Write your thesis after seeing the Evidence Pack and Agent Assessment.")
    print("Type END on a new line when finished.\n")
    thesis_lines = []
    while True:
        line = input()
        if line.strip() == "END":
            break
        thesis_lines.append(line)
    thesis = "\n".join(thesis_lines).strip()

    print("\nRunning adversarial Thesis Challenger...")
    challenge = call_llm(
        thesis_challenger_prompt(
            ctx.name,
            evidence_pack,
            scorecard,
            belief_as_text(prior),
            belief_as_text(post_ep),
            thesis,
        ),
        reasoning_effort="high",
    )
    print_section("THESIS CHALLENGER", challenge)
    save_text("thesis_challenge", ctx.name, challenge)

    # p3: final belief after adversarial challenge.
    final_belief = ask_belief_snapshot(
        "FINAL INVESTOR BELIEF — AFTER THESIS CHALLENGE (p3)"
    )

    print("\n=== FINAL HUMAN DECISION ===")
    decision = input("Position (PASS / SMALL / MODERATE / HIGH): ").strip().upper()
    decision_notes = input("Brief reason for final position: ").strip()
    final_decision = f"{decision} — {decision_notes}"

    print("\nDrafting memo without changing the human decision...")
    memo = call_llm(
        memo_prompt(
            ctx.name,
            ctx.mode,
            ctx.cutoff_date,
            evidence_pack,
            scorecard,
            thesis,
            challenge,
            belief_as_text(final_belief),
            final_decision,
        ),
        reasoning_effort="medium",
    )
    memo_path = save_text("investment_memo", ctx.name, memo)
    print_section("INVESTMENT MEMO", memo)

    payload = {
        "framework_version": FRAMEWORK_VERSION,
        "company": {
            "name": ctx.name,
            "url": ctx.url,
            "mode": ctx.mode,
            "cutoff_date": ctx.cutoff_date,
        },
        "beliefs": {
            "p1_prior": prior.to_dict(),
            "p2_after_evidence": post_ep.to_dict(),
            "p3_after_challenge": final_belief.to_dict(),
        },
        "belief_revision_best_estimate_pp": {
            "survival_p2_minus_p1": post_ep.survival_3y.best - prior.survival_3y.best,
            "survival_p3_minus_p2": final_belief.survival_3y.best - post_ep.survival_3y.best,
            "sustainable_given_survival_p2_minus_p1": (
                post_ep.sustainable_given_survival.best
                - prior.sustainable_given_survival.best
            ),
            "sustainable_given_survival_p3_minus_p2": (
                final_belief.sustainable_given_survival.best
                - post_ep.sustainable_given_survival.best
            ),
        },
        "thesis": thesis,
        "final_decision": final_decision,
    }
    session_path = save_json(ctx.name, payload)

    print("\nDONE")
    print(f"Investment memo: {memo_path}")
    print(f"Session data:    {session_path}")
    print("Other intermediate outputs are in ./outputs/")


if __name__ == "__main__":
    main()
