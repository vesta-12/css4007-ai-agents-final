import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import evidence


class EvidenceTests(unittest.TestCase):
    def test_rubric_citation_matches_file(self):
        item, = evidence.find_evidence(
            "bondscope", "rubric.md", "СПРЕД"
        )["evidence"]

        lines = (ROOT / "cases/bondscope/rubric.md").read_text().splitlines()
        self.assertEqual(item["quote"], lines[item["line"] - 1])
        self.assertIn("| 20 |", item["quote"])

    def test_header_only(self):
        result = evidence.find_evidence("bondscope", "daily_summary.csv", "")

        self.assertEqual([x["line"] for x in result["evidence"]], [1])
        self.assertIn("indicative_price", result["evidence"][0]["quote"])

    def test_variants(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / "cases/bondscope"
            shutil.copytree(ROOT / "cases/bondscope", folder)

            rubric = folder / "rubric.md"
            rubric.write_text(
                "\n".join(
                    line
                    for line in rubric.read_text().splitlines()
                    if "спред" not in line.lower()
                )
            )
            (folder / "trade_register.csv").unlink()

            with patch.object(evidence.bondscope, "ROOT", Path(tmp).resolve()):
                self.assertEqual(
                    evidence.find_evidence("bondscope", "rubric.md", "спред")["status"],
                    "no_match",
                )
                self.assertEqual(
                    evidence.find_evidence("bondscope", "trade_register.csv", "")["status"],
                    "unavailable",
                )

    def test_review_validates_model_references(self):
        client = Mock()
        message = Mock()
        client.chat.completions.create.return_value.choices = [Mock(message=message)]

        report = {
            "status": "no_issue",  # Contradictory model label from the live run.
            "spread_requirement": "required",
            "spread_inputs": "insufficient",
            "finding": "Finding",
            "impact": "Impact",
            "next_action": "Action",
            "evidence": [
                "rubric.md:7",
                "brief.md:13",
                "daily_summary.csv:1",
                "trade_register.csv:1",
            ],
        }

        message.content = json.dumps(report)
        result = evidence.review(client, "test-model")
        self.assertEqual(result["status"], "confirmed")
        self.assertIn("снимки заявок", result["evidence"][1]["quote"])

        report["evidence"][0] = "rubric.md:999"
        message.content = json.dumps(report)
        with self.assertRaisesRegex(ValueError, "Invalid evidence reference"):
            evidence.review(client, "test-model")

    def test_review_status_variants(self):
        cases = [
            ("not_required", "insufficient", "found", "no_issue"),
            ("required", "sufficient", "found", "no_issue"),
            ("required", "insufficient", "unavailable", "incomplete"),
            ("required", "unknown", "found", "incomplete"),
            ("unknown", "insufficient", "found", "incomplete"),
        ]
        for requirement, inputs, source, expected in cases:
            with self.subTest(requirement=requirement, inputs=inputs, source=source):
                facts = {"spread_requirement": requirement, "spread_inputs": inputs}
                self.assertEqual(evidence.review_status(facts, {"table": source}), expected)

    def test_reference_outside_case(self):
        with self.assertRaises(ValueError):
            evidence.find_evidence(
                "bondscope", "../../evaluation/bondscope/expected_findings.md", ""
            )


if __name__ == "__main__":
    unittest.main()
