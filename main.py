# main.py
"""
Entry point for the LangGraph Multi-Agent Research Assistant.

Usage:
    python main.py --topic "Applications of AI in Healthcare"
    python main.py --topic "X" --mode web --save samples/output.md

Notes:
- Reads SEARCH_MODE, GEMINI_API_KEY, GEMINI_MODEL from .env (if present).
- If langgraph is not installed, the workflow falls back to a sequential runner.
"""
import argparse
import os
from datetime import datetime
from dotenv import load_dotenv

# load .env
load_dotenv()

from langgraph_workflow import LangGraphResearchWorkflow  # local workflow wrapper

def pretty_print_report(report_text: str):
    sep = "\n" + "="*80 + "\n"
    print(sep)
    print(report_text)
    print(sep)

def save_report(report_text: str, path: str):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(report_text)
    print(f"[Saved] Report written to: {path}")

def main():
    parser = argparse.ArgumentParser(description="Run the LangGraph Research Assistant")
    parser.add_argument("--topic", type=str, required=True, help="Research topic to run the pipeline on")
    parser.add_argument("--mode", choices=["mock", "web"], default=None,
                        help="Search mode: 'mock' (default or env SEARCH_MODE) or 'web' (live scraping)")
    parser.add_argument("--max_results", type=int, default=5, help="Max search results / documents")
    parser.add_argument("--no_polish", action="store_true", help="Disable Gemini polish in ReportAgent")
    parser.add_argument("--save", type=str, default=None, help="Path to save the final report (e.g. samples/report.md)")
    args = parser.parse_args()

    # Determine search mode: CLI > .env > default 'mock'
    search_mode = args.mode or os.getenv("SEARCH_MODE", "mock")
    polish_with_gemini = not args.no_polish

    print(f"[INFO] Topic: {args.topic}")
    print(f"[INFO] Search mode: {search_mode}")
    print(f"[INFO] Polish with Gemini: {polish_with_gemini}")

    # Initialize workflow
    wf = LangGraphResearchWorkflow(search_mode)

    # Run workflow
    try:
        result = wf.run(
            args.topic,
            max_results=args.max_results,
            polish_with_gemini=polish_with_gemini,
            max_output_tokens=int(os.getenv("SUMMARIZER_MAX_TOKENS", 300)),
            gemini_max_output_tokens=int(os.getenv("GEMINI_MAX_TOKENS", 800)),
        )
    except Exception as e:
        print(f"[ERROR] Workflow execution failed: {e}")
        raise

    # result may be dict or nested; ensure we extract the report text
    if isinstance(result, dict):
        report_text = result.get("report") if result.get("report") else result.get("report", str(result))
        # if report is itself a dict with text
        if isinstance(report_text, dict) and "report" in report_text:
            report_text = report_text["report"]
    else:
        report_text = str(result)

    # Print result
    pretty_print_report(report_text)

    # Optionally save
    if args.save:
        # add metadata header
        header = (
            f"# Report: {args.topic}\n"
            f"# Generated: {datetime.utcnow().isoformat()} UTC\n\n"
        )
        save_report(header + report_text, args.save)


if __name__ == "__main__":
    main()
from typing import List, Dict 