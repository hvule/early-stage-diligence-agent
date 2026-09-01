# Early-Stage Diligence Agent v0.2

Human-in-the-loop early-stage investment diligence prototype using Framework v1.2.

## Workflow

1. Choose live diligence or historical backtest.
2. Enter company name / optional URL.
3. Investor records a pre-evidence subjective probability range (p1).
4. Agent performs web research and shows the source report.
5. Investor may supplement the source set with pasted text, URLs, PDFs, DOCX, TXT/MD/CSV files.
6. Agent builds an Evidence Pack.
7. Investor records post-evidence belief (p2).
8. Agent scores the ten Framework v1.2 dimensions.
9. Investor writes the investment thesis.
10. Agent adversarially challenges the thesis.
11. Investor records final belief (p3) and position size.
12. Agent drafts a memo that preserves the human decision.

## Install

```bash
python -m venv .venv
source .venv/bin/activate      # macOS/Linux
# .venv\\Scripts\\activate   # Windows PowerShell

pip install -r requirements.txt
```

## API key

macOS/Linux:

```bash
export OPENAI_API_KEY="your_openai_api_key_here"
```

Windows PowerShell:

```powershell
$env:OPENAI_API_KEY="YOUR_KEY"
```

Optional model override:

```bash
export OPENAI_MODEL="gpt-5.6"
```

## Run

```bash
python main.py
```

## Notes

- Historical mode is an epistemic backtest, not a guaranteed perfect time machine. The research prompt enforces the cutoff and tells the model not to use post-cutoff outcome knowledge; you should still inspect the source register for leakage.
- Probability ranges are subjective investor belief ranges, not statistical confidence intervals.
- The system intentionally keeps the final investment decision with the human investor.



