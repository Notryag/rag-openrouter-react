#!/usr/bin/env python3
"""Run lightweight RAG evaluation against the local /chat API."""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional
from urllib import error, request


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATASET = ROOT / "backend" / "eval" / "qa_dataset.jsonl"
DEFAULT_REPORT = ROOT / "backend" / "eval" / "last_report.json"


@dataclass
class EvalCase:
    case_id: str
    question: str
    expected_keywords: list[str]
    expected_sources: list[str]


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    rank = int(math.ceil((p / 100.0) * len(values))) - 1
    rank = max(0, min(rank, len(values) - 1))
    return sorted(values)[rank]


def post_json(url: str, payload: dict[str, Any], token: Optional[str] = None) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = request.Request(url, data=body, headers=headers, method="POST")
    with request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def login(api_base: str, username: str, password: str) -> str:
    data = post_json(
        f"{api_base}/auth/login",
        {"username": username, "password": password},
    )
    token = data.get("access_token")
    if not token:
        raise RuntimeError("Login succeeded but access_token is missing.")
    return token


def load_cases(path: Path) -> list[EvalCase]:
    rows: list[EvalCase] = []
    with path.open("r", encoding="utf-8") as f:
        for idx, line in enumerate(f, start=1):
            raw = line.strip()
            if not raw:
                continue
            item = json.loads(raw)
            case_id = item.get("id")
            question = item.get("question")
            expected_keywords = item.get("expected_keywords", [])
            expected_sources = item.get("expected_sources", [])
            if not case_id or not question or not isinstance(expected_keywords, list):
                raise ValueError(f"Invalid dataset row {idx}: missing required fields")
            rows.append(
                EvalCase(
                    case_id=str(case_id),
                    question=str(question),
                    expected_keywords=[str(x).lower() for x in expected_keywords],
                    expected_sources=[str(x).lower() for x in expected_sources],
                )
            )
    if not rows:
        raise ValueError("Dataset is empty.")
    return rows


def evaluate_answer(case: EvalCase, answer: str, sources: list[str]) -> tuple[bool, Optional[bool], list[str]]:
    lower_answer = answer.lower()
    missing_keywords = [kw for kw in case.expected_keywords if kw not in lower_answer]
    keyword_pass = len(missing_keywords) == 0

    citation_pass: Optional[bool] = None
    if case.expected_sources:
        citation_pass = any(
            expected in source.lower()
            for expected in case.expected_sources
            for source in sources
        )

    final_pass = keyword_pass and (citation_pass is not False)
    return final_pass, citation_pass, missing_keywords


def main() -> int:
    parser = argparse.ArgumentParser(description="Run RAG evaluation cases against /chat.")
    parser.add_argument("--dataset", default=str(DEFAULT_DATASET), help="Path to JSONL eval dataset.")
    parser.add_argument("--api-base", default="http://localhost:8000", help="Backend API base URL.")
    parser.add_argument("--k", type=int, default=4, help="Retriever top-k for /chat.")
    parser.add_argument("--limit", type=int, default=0, help="Only run first N cases (0 means all).")
    parser.add_argument("--token", default="", help="Bearer token for authenticated calls.")
    parser.add_argument("--username", default="", help="Username for auto-login.")
    parser.add_argument("--password", default="", help="Password for auto-login.")
    parser.add_argument("--dry-run", action="store_true", help="Only validate dataset and exit.")
    parser.add_argument("--report", default=str(DEFAULT_REPORT), help="Output JSON report path.")
    args = parser.parse_args()

    dataset_path = Path(args.dataset)
    report_path = Path(args.report)
    cases = load_cases(dataset_path)
    if args.limit > 0:
        cases = cases[: args.limit]

    if args.dry_run:
        print(f"Dataset OK: {len(cases)} cases loaded from {dataset_path}")
        return 0

    token = args.token.strip() or None
    if args.username:
        if not args.password:
            raise ValueError("When --username is provided, --password is required.")
        token = login(args.api_base, args.username, args.password)

    results: list[dict[str, Any]] = []
    latencies: list[float] = []
    citation_total = 0
    citation_hits = 0

    for case in cases:
        started = time.perf_counter()
        try:
            response = post_json(
                f"{args.api_base}/chat",
                {"question": case.question, "k": args.k},
                token=token,
            )
            elapsed_ms = (time.perf_counter() - started) * 1000.0
            latencies.append(elapsed_ms)
            answer = str(response.get("answer", ""))
            raw_sources = response.get("sources", [])
            source_paths = [str(item.get("source", "")) for item in raw_sources if isinstance(item, dict)]

            passed, citation_pass, missing = evaluate_answer(case, answer, source_paths)
            if citation_pass is not None:
                citation_total += 1
                citation_hits += 1 if citation_pass else 0

            results.append(
                {
                    "id": case.case_id,
                    "pass": passed,
                    "latency_ms": round(elapsed_ms, 2),
                    "missing_keywords": missing,
                    "citation_pass": citation_pass,
                    "answer_preview": answer[:180],
                    "sources": source_paths,
                }
            )
            print(f"[{'PASS' if passed else 'FAIL'}] {case.case_id} ({elapsed_ms:.1f} ms)")
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            results.append(
                {
                    "id": case.case_id,
                    "pass": False,
                    "latency_ms": 0.0,
                    "missing_keywords": case.expected_keywords,
                    "citation_pass": False if case.expected_sources else None,
                    "error": f"HTTP {exc.code}: {detail}",
                }
            )
            print(f"[FAIL] {case.case_id} (HTTP {exc.code})")
        except Exception as exc:
            results.append(
                {
                    "id": case.case_id,
                    "pass": False,
                    "latency_ms": 0.0,
                    "missing_keywords": case.expected_keywords,
                    "citation_pass": False if case.expected_sources else None,
                    "error": str(exc),
                }
            )
            print(f"[FAIL] {case.case_id} ({exc})")

    total = len(results)
    passed_total = sum(1 for r in results if r["pass"])
    answer_correctness = (passed_total / total) if total else 0.0
    citation_precision = (citation_hits / citation_total) if citation_total else 0.0
    p95_latency = percentile(latencies, 95)

    summary = {
        "total_cases": total,
        "passed_cases": passed_total,
        "answer_correctness": round(answer_correctness, 4),
        "citation_precision": round(citation_precision, 4),
        "p95_latency_ms": round(p95_latency, 2),
    }
    report = {
        "dataset": str(dataset_path),
        "api_base": args.api_base,
        "k": args.k,
        "summary": summary,
        "results": results,
    }

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("\nSummary:")
    print(json.dumps(summary, indent=2))
    print(f"Report saved to: {report_path}")

    return 0 if passed_total == total else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        sys.exit(130)
