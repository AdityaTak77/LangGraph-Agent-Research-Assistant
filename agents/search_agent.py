# agents/search_agent.py
from typing import List, Dict

class SearchAgent:
    """SearchAgent: accept a topic string and return a list of "documents".
    This implementation offers two modes:
      - mock: returns curated mock documents
      - web: performs a simple requests+bs4 search (rudimentary)
    """

    def __init__(self, mode: str = "mock"):
        assert mode in ("mock", "web")
        self.mode = mode

    def search(self, topic: str, max_results: int = 5) -> List[Dict]:
        """Return a list of dicts: {"title":..., "source":..., "text":...}
        """
        if self.mode == "mock":
            return self._mock_results(topic)
        else:
            return self._web_search(topic, max_results)

    def _mock_results(self, topic: str):
        # simple static documents — replace with real fetch in production
        docs = [
            {
                "title": "AI for Radiology",
                "source": "MockPaper1",
                "text": (
                    "AI helps detect anomalies in X-rays and MRIs using CNNs. "
                    "Clinical workflows often combine image pre-processing and model explainability."
                ),
            },
            {
                "title": "AI for Drug Discovery",
                "source": "MockPaper2",
                "text": (
                    "Deep learning and graph neural networks speed up candidate screening, "
                    "helping predict molecular properties and binding affinities."
                ),
            },
            {
                "title": "AI for Clinical Decision Support",
                "source": "MockPaper3",
                "text": (
                    "Predictive models for patient readmission, triage prioritization, and personalized treatment recommendations."
                ),
            },
        ]
        return docs

    def _web_search(self, topic: str, max_results: int = 5):
        # Very minimal example — for serious use integrate a search API
        from utils.web_search import simple_web_search
        return simple_web_search(topic, max_results)