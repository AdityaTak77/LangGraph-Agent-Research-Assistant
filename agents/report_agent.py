# agents/report_agent.py
"""
ReportAgent: combine summaries into a well-structured final report.

Behavior:
- If GEMINI_API_KEY is present in environment, the agent will ask Gemini (model
  specified by GEMINI_MODEL) to rewrite the assembled report into a polished,
  well-structured final form.
- If no API key is present, the agent will assemble a structured plain-text report.

Dependencies:
- python-dotenv (for .env support)
- (optional) google-generativeai for Gemini polish step:
    pip install google-generativeai
"""

import os
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Try optional import for Gemini API
try:
    import google.generativeai as genai  # type: ignore
    _HAS_GENAI = True
except Exception:
    genai = None  # type: ignore
    _HAS_GENAI = False

load_dotenv()


class ReportAgent:
    def __init__(self, style: str = "formal", gemini_model_env: str = "GEMINI_MODEL"):
        """
        Args:
            style: "formal" | "concise" | "technical" (affects local assembly wording)
            gemini_model_env: environment variable name for model, default GEMINI_MODEL
        """
        self.style = style
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.gemini_model_name = os.getenv(gemini_model_env, os.getenv("GEMINI_MODEL", "gemini-2.0-flash"))
        self.use_gemini = bool(self.gemini_api_key and _HAS_GENAI)
        if self.gemini_api_key and _HAS_GENAI:
            genai.configure(api_key=self.gemini_api_key)
            # create model handle lazily on first use to avoid import-time failures
            self._model = genai.GenerativeModel(self.gemini_model_name)
        else:
            self._model = None

    def build_report(self, topic: str, summaries: List[Dict], polish_with_gemini: bool = True,
                     gemini_max_output_tokens: int = 800) -> Dict:
        """
        Build the final report.

        Args:
            topic: user topic string
            summaries: list of dicts {"title", "source", "summary"}
            polish_with_gemini: whether to attempt a Gemini polish (only if configured)
            gemini_max_output_tokens: token cap for Gemini finalization

        Returns:
            dict: {
                "topic": topic,
                "report": "<final report text>",
                "sections": { ... }   # assembled sections before polish
            }
        """
        # 1) Create structured sections locally
        sections = self._assemble_sections(topic, summaries)

        # 2) If requested and available, polish with Gemini
        if polish_with_gemini and self.use_gemini and self._model is not None:
            try:
                prompt = self._build_polish_prompt(topic, sections)
                response = self._model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        max_output_tokens=gemini_max_output_tokens,
                        temperature=0.1,
                    ),
                )
                polished = response.text.strip() if getattr(response, "text", None) else ""
                if polished:
                    return {"topic": topic, "report": polished, "sections": sections}
            except Exception as e:
                # On error, fall back to assembled report
                fallback_text = f"[Gemini polish failed: {e}]\n\n" + self._combine_sections_text(sections)
                return {"topic": topic, "report": fallback_text, "sections": sections}

        # 3) Fallback: return the locally-assembled report text
        plain_report = self._combine_sections_text(sections)
        return {"topic": topic, "report": plain_report, "sections": sections}

    def _assemble_sections(self, topic: str, summaries: List[Dict]) -> Dict[str, str]:
        # Abstract: one-sentence summary synthesized from summaries (simple heuristic)
        abstract = self._make_abstract(topic, summaries)

        # Overview: bullet list of source summaries
        overview_lines = []
        for s in summaries:
            title = s.get("title", "Untitled")
            src = s.get("source", "Unknown")
            summ = s.get("summary", "").replace("\n", " ")
            overview_lines.append(f"- {title} ({src}): {summ}")
        overview = "\n".join(overview_lines) if overview_lines else "No sources available."

        # Applications: extract likely application buckets heuristically
        applications = self._infer_applications(summaries)

        # Limitations: produce a concise limitations section
        limitations = (
            "- Data bias and generalization risks\n"
            "- Need for clinical trials, validation, and regulatory approval\n"
            "- Explainability and integration into clinical workflows\n"
            "- Privacy, security, and data governance concerns"
        )

        # Conclusion & Recommendations: simple heuristic
        conclusions = self._make_conclusions(summaries)

        sections = {
            "abstract": abstract,
            "overview": overview,
            "applications": applications,
            "limitations": limitations,
            "conclusions": conclusions,
        }
        return sections

    def _make_abstract(self, topic: str, summaries: List[Dict]) -> str:
        # Combine important phrases from summaries (simple join and shorten)
        snippets = []
        for s in summaries:
            txt = s.get("summary", "")
            if txt:
                snippets.append(txt)
        combined = " ".join(snippets)[:800]  # limit size
        if not combined:
            return f"Abstract:\nThis report provides an overview of research related to '{topic}'."
        # craft a one-sentence abstract
        return f"Abstract:\nThis report on '{topic}' synthesizes findings from multiple sources, " \
               f"highlighting key applications, methods, and limitations."

    def _infer_applications(self, summaries: List[Dict]) -> str:
        apps = set()
        for s in summaries:
            text = (s.get("summary") or "").lower()
            if any(k in text for k in ("radiology", "imaging", "x-ray", "mri", "ct")):
                apps.add("Medical imaging / Radiology")
            if any(k in text for k in ("drug", "molecule", "molecular", "gcn", "graph neural")):
                apps.add("Drug discovery & molecular screening")
            if any(k in text for k in ("triage", "readmission", "prediction", "risk score", "clinical decision")):
                apps.add("Clinical decision support & risk prediction")
            if any(k in text for k in ("ehr", "electronic health", "patient record", "notes")):
                apps.add("Clinical documentation & EHR summarization")
            if any(k in text for k in ("robot", "surgery", "surgical", "robotic")):
                apps.add("Robotics & surgical assistance")
        if not apps:
            apps.add("General clinical decision support and workflow automation")
        return "Applications:\n- " + "\n- ".join(sorted(apps))

    def _make_conclusions(self, summaries: List[Dict]) -> str:
        return (
            "Conclusions & Recommendations:\n"
            "- AI shows promise across imaging, drug discovery, and clinical decision support.\n"
            "- Stakeholders should prioritize robust validation, fairness audits, and explainability.\n"
            "- Integration into clinical workflows and regulatory alignment are essential for adoption."
        )

    def _combine_sections_text(self, sections: Dict[str, str]) -> str:
        parts = [
            sections.get("abstract", ""),
            "Overview of sources:",
            sections.get("overview", ""),
            sections.get("applications", ""),
            "Limitations and considerations:",
            sections.get("limitations", ""),
            sections.get("conclusions", ""),
        ]
        return "\n\n".join([p for p in parts if p])

    def _build_polish_prompt(self, topic: str, sections: Dict[str, str]) -> str:
        """
        Build a single prompt requesting the model to rewrite and format the report.
        """
        assembled = self._combine_sections_text(sections)
        prompt = (
            "You are an expert research writer. Take the raw assembled report below and rewrite it "
            "into a concise, well-structured professional report with headings, short paragraphs, "
            "and bullet lists where helpful. Keep the report 3-6 sections long. Use a formal tone.\n\n"
            f"Topic: {topic}\n\n"
            "Raw assembled content:\n"
            "----\n"
            f"{assembled}\n"
            "----\n\n"
            "Deliver the final report in plain text. Include an executive summary (2-3 sentences) at the top, "
            "then the sections: Overview, Applications, Limitations, Conclusions & Recommendations. "
            "Be succinct and avoid repeating phrases."
        )
        return prompt


# ============== Example test run ==============
if __name__ == "__main__":
    sample_summaries = [
        {"title": "AI for Radiology", "source": "MockPaper1", "summary": "Deep CNNs improve detection of anomalies in X-rays and MRIs, increasing diagnostic speed."},
        {"title": "AI for Drug Discovery", "source": "MockPaper2", "summary": "GNNs and deep learning accelerate candidate screening and property prediction for molecules."},
        {"title": "Clinical Decision Support", "source": "MockPaper3", "summary": "Predictive models can identify high-risk patients for readmission and assist triage."},
    ]

    agent = ReportAgent()
    out = agent.build_report("Applications of AI in Healthcare", sample_summaries, polish_with_gemini=True)
    print("=== FINAL REPORT ===\n")
    print(out["report"])