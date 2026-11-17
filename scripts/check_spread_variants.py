"""Run two independent live BondScope checks. Execute from the project root."""
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import evidence


def run_variant(client, model, variant):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp).resolve()
        folder = root / "cases" / "bondscope"
        shutil.copytree(ROOT / "cases" / "bondscope", folder)
        if variant == "without_spread_criterion":
            rubric = folder / "rubric.md"
            lines = rubric.read_text(encoding="utf-8").splitlines(keepends=True)
            kept = [line for line in lines if not line.startswith("| Расчёт спреда |")]
            if len(lines) - len(kept) != 1:
                raise ValueError("Expected one spread criterion in the original rubric")
            rubric.write_text("".join(kept), encoding="utf-8")
            requirement, status, availability = "not_required", "no_issue", "found"
        elif variant == "without_trade_register":
            (folder / "trade_register.csv").unlink()
            requirement, status, availability = "required", "incomplete", "unavailable"
        else:
            raise ValueError("Unknown variant")

        with patch.object(evidence.bondscope, "ROOT", root):
            report = evidence.review(client, model)

    cited = {item["file"] for item in report["evidence"]}
    expected_sources = {name: "found" for name in evidence.DOCUMENTS + evidence.TABLES}
    expected_sources["trade_register.csv"] = availability
    checks = {
        "requirement": report["spread_requirement"] == requirement,
        "status": report["status"] == status,
        "source_availability": report["sources"] == expected_sources,
        "rubric_cited": "rubric.md" in cited,
        "available_citations_only": all(expected_sources.get(name) == "found" for name in cited),
    }
    if variant == "without_trade_register":
        checks["coverage_unknown"] = report["spread_inputs"] == "unknown"
        checks["missing_file_requested"] = "trade_register.csv" in report["next_action"]
    return {"variant": variant, "checks": checks, "report": report}


def main():
    from dotenv import load_dotenv
    from openai import APIError, OpenAI

    load_dotenv(ROOT / ".env")
    key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not key:
        raise SystemExit("Set LLM_API_KEY in the project .env file.")
    model = os.getenv("LLM_MODEL") or "gpt-4.1-mini"
    results = []
    with OpenAI(api_key=key, timeout=45, max_retries=1) as client:
        for variant in ("without_spread_criterion", "without_trade_register"):
            try:
                result = run_variant(client, model, variant)
            except APIError as exc:
                result = {"variant": variant, "error": type(exc).__name__}
            except (ValueError, OSError) as exc:
                result = {"variant": variant, "error": str(exc)}
            results.append(result)
    print(json.dumps({"model": model, "question": evidence.QUESTION, "results": results},
                     ensure_ascii=False, indent=2))
    if not all("checks" in result and all(result["checks"].values()) for result in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
