import json
from pathlib import Path

EXAMPLES_DIR = Path("examples/n8n")
WORKFLOW_FILES = (
    "01-capture-via-api.json",
    "02-seiton-webhook-events.json",
    "03-todoist-to-capture.json",
    "04-knowledge-backend-on-indexed.json",
    "05-multi-llm-enrich-then-capture.json",
)


def test_n8n_example_workflows_are_valid_json():
    for filename in WORKFLOW_FILES:
        path = EXAMPLES_DIR / filename
        assert path.is_file(), f"missing workflow: {filename}"
        data = json.loads(path.read_text(encoding="utf-8"))
        assert isinstance(data.get("nodes"), list) and data["nodes"]
        assert isinstance(data.get("connections"), dict)
        assert data.get("name")


def test_n8n_capture_workflow_has_http_request_to_v1_capture():
    data = json.loads((EXAMPLES_DIR / "01-capture-via-api.json").read_text(encoding="utf-8"))
    http_nodes = [n for n in data["nodes"] if n["type"] == "n8n-nodes-base.httpRequest"]
    assert len(http_nodes) == 1
    assert "/v1/capture" in http_nodes[0]["parameters"]["url"]
    headers = http_nodes[0]["parameters"]["headerParameters"]["parameters"]
    assert any(h["name"] == "X-Seiton-Api-Key" for h in headers)


def test_n8n_webhook_workflow_has_webhook_and_switch():
    data = json.loads((EXAMPLES_DIR / "02-seiton-webhook-events.json").read_text(encoding="utf-8"))
    types = {n["type"] for n in data["nodes"]}
    assert "n8n-nodes-base.webhook" in types
    assert "n8n-nodes-base.switch" in types


def test_n8n_knowledge_workflow_searches_semantically():
    data = json.loads(
        (EXAMPLES_DIR / "04-knowledge-backend-on-indexed.json").read_text(encoding="utf-8")
    )
    http_nodes = [n for n in data["nodes"] if n["type"] == "n8n-nodes-base.httpRequest"]
    assert len(http_nodes) == 1
    assert "/v1/notes/search" in http_nodes[0]["parameters"]["url"]
    assert "semantic=true" in http_nodes[0]["parameters"]["url"]


def test_n8n_multi_llm_workflow_calls_ollama_then_capture():
    data = json.loads(
        (EXAMPLES_DIR / "05-multi-llm-enrich-then-capture.json").read_text(encoding="utf-8")
    )
    http_nodes = [n for n in data["nodes"] if n["type"] == "n8n-nodes-base.httpRequest"]
    assert len(http_nodes) == 2
    urls = [n["parameters"]["url"] for n in http_nodes]
    assert any("/v1/chat/completions" in u for u in urls)
    assert any("/v1/capture" in u for u in urls)
    capture = next(n for n in http_nodes if "/v1/capture" in n["parameters"]["url"])
    headers = capture["parameters"]["headerParameters"]["parameters"]
    assert any(h["name"] == "X-Seiton-Api-Key" for h in headers)
    # Ollama → Extract → Capture verdrahtet
    assert "Ollama anreichern" in data["connections"]
    assert "Antwort extrahieren" in data["connections"]
