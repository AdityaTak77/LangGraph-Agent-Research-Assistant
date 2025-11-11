# langgraph_workflow.py
"""
LangGraph workflow wrapper for the Research Assistant.

Behavior:
- If `langgraph` package is installed, this builds a Graph with three nodes:
  search -> summarize -> report
- If `langgraph` is not available, it falls back to a simple sequential runner
  that calls the same agent methods in order.

Agents expected to exist under agents/:
  - agents.search_agent.SearchAgent
  - agents.summarizer_agent.SummarizerAgent
  - agents.report_agent.ReportAgent

Environment:
  - SEARCH_MODE (optional): "mock" or "web" (default: "mock")
  - GEMINI_MODEL / GEMINI_API_KEY used by the summarizer if present

Example:
    wf = LangGraphResearchWorkflow()
    report = wf.run("Applications of AI in Healthcare")
    print(report["report"])
"""
from typing import Dict, Any, Optional
import os
from dotenv import load_dotenv

load_dotenv()

# Import agents
from agents.search_agent import SearchAgent
from agents.summarizer_agent import SummarizerAgent
from agents.report_agent import ReportAgent

# Try to import langgraph; if unavailable, we'll use a fallback runner.
try:
    from langgraph import Graph, Node  # type: ignore
    _HAS_LANGGRAPH = True
except Exception:
    Graph = None  # type: ignore
    Node = None  # type: ignore
    _HAS_LANGGRAPH = False


class LangGraphResearchWorkflow:
    def __init__(self, search_mode: Optional[str] = None):
        """
        Initialize agents and (optionally) a LangGraph graph.
        Args:
            search_mode: "mock" or "web". If None, read from env SEARCH_MODE or default to "mock".
        """
        if search_mode is None:
            search_mode = os.getenv("SEARCH_MODE", "mock")

        # initialize agents
        self.search_agent = SearchAgent(mode=search_mode)
        self.summarizer_agent = SummarizerAgent()  # uses GEMINI_MODEL / GEMINI_API_KEY from env
        self.report_agent = ReportAgent()

        # If langgraph is available build nodes/graph, otherwise keep None
        self.graph = None
        if _HAS_LANGGRAPH:
            try:
                self.graph = Graph(name="research_workflow")
                # Create nodes - using callables that accept and return dicts
                self.node_search = Node(name="search", func=self._node_search)
                self.node_summarize = Node(name="summarize", func=self._node_summarize)
                self.node_report = Node(name="report", func=self._node_report)

                for n in (self.node_search, self.node_summarize, self.node_report):
                    self.graph.add_node(n)
                # Add edges: search -> summarize -> report
                self.graph.add_edge(self.node_search, self.node_summarize)
                self.graph.add_edge(self.node_summarize, self.node_report)
            except Exception:
                # If any Graph creation issue occurs, fall back silently to sequential runner
                self.graph = None

    # Node wrapper functions: they accept a dict of inputs and return dict outputs
    def _node_search(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        topic = inputs.get("topic", "")
        max_results = inputs.get("max_results", 5)
        docs = self.search_agent.search(topic, max_results=max_results)
        return {"docs": docs}

    def _node_summarize(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        docs = inputs.get("docs", [])
        # Optionally allow summarizer-specific kwargs via inputs
        max_output_tokens = inputs.get("max_output_tokens", 300)
        summaries = self.summarizer_agent.summarize_docs(docs, max_output_tokens=max_output_tokens)
        return {"summaries": summaries}

    def _node_report(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        topic = inputs.get("topic", "")
        summaries = inputs.get("summaries", [])
        polish_with_gemini = inputs.get("polish_with_gemini", True)
        gemini_max = inputs.get("gemini_max_output_tokens", 800)
        report = self.report_agent.build_report(topic, summaries, polish_with_gemini=polish_with_gemini,
                                                gemini_max_output_tokens=gemini_max)
        return {"report": report}

    def run(self, topic: str, max_results: int = 5, polish_with_gemini: bool = True,
            max_output_tokens: int = 300, gemini_max_output_tokens: int = 800) -> Dict[str, Any]:
        """
        Execute the workflow and return the final report dict.

        Args:
            topic: research topic string
            max_results: how many search results to fetch
            polish_with_gemini: whether to try model polishing in ReportAgent
            max_output_tokens: summarizer token cap per doc
            gemini_max_output_tokens: report polishing token cap

        Returns:
            dict containing "topic", "report" (text), and optionally "sections"
        """
        inputs = {
            "topic": topic,
            "max_results": max_results,
            "polish_with_gemini": polish_with_gemini,
            "max_output_tokens": max_output_tokens,
            "gemini_max_output_tokens": gemini_max_output_tokens,
        }

        if self.graph is not None:
            # If a real LangGraph graph exists, attempt to execute it.
            # Note: exact Graph API for execution may differ across LangGraph versions.
            # We'll try a generic approach: run nodes sequentially by invoking their functions.
            try:
                out1 = self.node_search.func(inputs) if hasattr(self.node_search, "func") else self._node_search(inputs)
                merged1 = {**inputs, **out1}
                out2 = self.node_summarize.func(merged1) if hasattr(self.node_summarize, "func") else self._node_summarize(merged1)
                merged2 = {**merged1, **out2}
                out3 = self.node_report.func(merged2) if hasattr(self.node_report, "func") else self._node_report(merged2)
                # out3 is {'report': {...}}
                return out3.get("report", out3)
            except Exception:
                # fallback to sequential runner below
                pass

        # Fallback sequential runner (works without langgraph)
        # 1) Search
        docs = self.search_agent.search(topic, max_results=max_results)
        # 2) Summarize
        summaries = self.summarizer_agent.summarize_docs(docs, max_output_tokens=max_output_tokens)
        # 3) Build report
        report = self.report_agent.build_report(topic, summaries, polish_with_gemini=polish_with_gemini,
                                                gemini_max_output_tokens=gemini_max_output_tokens)
        return report


# ========== Example usage ==========
if __name__ == "__main__":
    # Quick demo when running this file directly
    wf = LangGraphResearchWorkflow()
    topic = "Applications of AI in Healthcare"
    result = wf.run(topic, max_results=3, polish_with_gemini=True)
    print("\n===== Generated Report =====\n")
    print(result["report"])
