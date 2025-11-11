# ==========================================
# agents/summarizer_agent.py
# ==========================================
import os
from typing import List, Dict
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables (.env file)
load_dotenv()

class SummarizerAgent:
    """
    SummarizerAgent — Uses Google's Gemini 2.0 Flash model to summarize documents.

    Requirements:
        pip install google-generativeai python-dotenv

    Environment Variables:
        GEMINI_API_KEY=<your Gemini API key>
        GEMINI_MODEL=gemini-2.0-flash  (default if not set)
    """

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

        if not api_key:
            raise ValueError("Missing GEMINI_API_KEY. Set it in your .env file or environment variables.")

        # Configure Gemini API client
        genai.configure(api_key=api_key)

        # Initialize the model
        self.model = genai.GenerativeModel(model_name)

    def summarize_docs(self, docs: List[Dict], max_output_tokens: int = 300) -> List[Dict]:
        """
        Summarize multiple documents using Gemini 2.0 Flash.

        Args:
            docs: List of dicts with fields "title", "source", and "text".
            max_output_tokens: Approximate cap for each summary.

        Returns:
            List of dicts with {"title", "source", "summary"}.
        """
        summaries = []

        for doc in docs:
            title = doc.get("title", "Untitled Document")
            source = doc.get("source", "Unknown Source")
            text = doc.get("text", "").strip()

            if not text:
                summaries.append({
                    "title": title,
                    "source": source,
                    "summary": "[No content provided]"
                })
                continue

            # Gemini summarization prompt
            prompt = (
                f"You are a helpful research assistant.\n\n"
                f"Summarize the following document in 2–4 sentences.\n"
                f"Highlight key findings, methods, and limitations.\n\n"
                f"Title: {title}\nSource: {source}\n\n{text}"
            )

            try:
                response = self.model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        max_output_tokens=max_output_tokens,
                        temperature=0.2,
                    ),
                )
                summary_text = response.text.strip() if response.text else "[No summary returned]"
            except Exception as e:
                summary_text = f"[Gemini API Error: {e}]"

            summaries.append({
                "title": title,
                "source": source,
                "summary": summary_text,
            })

        return summaries


# ============== Example test run ==============
if __name__ == "__main__":
    docs = [
        {
            "title": "AI in Healthcare Diagnostics",
            "source": "SampleSource",
            "text": (
                "AI models assist doctors in diagnosing diseases earlier and more accurately. "
                "Gemini 2.0 Flash improves efficiency in generating medical summaries and insights "
                "from unstructured patient data."
            ),
        }
    ]

    summarizer = SummarizerAgent()
    result = summarizer.summarize_docs(docs)
    print(result)
