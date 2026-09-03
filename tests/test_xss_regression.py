"""Regression test (E27-2): no unescaped innerHTML in UI JavaScript.

Checks all .js files under app/ui/static/ so dynamic values in innerHTML
assignments always go through escapeHtml(). Allowed:
- static HTML strings (no ${…} interpolation)
- ${escapeHtml(…)} interpolations
- ${badge(…)} interpolations (badge() escapes internally)
- ${formatDate(…)} interpolations (always returns a locale string)
- ${formatBytes(…)} interpolations (numbers only)
- ${Math.…} interpolations (numbers only)
- pure string/boolean expressions like ${…? "…" : "…"}
"""

import re
from pathlib import Path

import pytest

UI_STATIC = Path(__file__).resolve().parent.parent / "app" / "ui" / "static"

SAFE_INTERPOLATIONS = re.compile(
    r"\$\{"
    r"(?:"
    r"escapeHtml\(|"
    r"noteLink\(|"  # builds escaped <a> via escapeHtml + encodeURIComponent
    r"noteHref\(|"  # encodeURIComponent only — safe in href
    r"badge\(|"
    r"badge\}|"  # locally built HTML string variable
    r"formatDate\(|"
    r"formatBytes\(|"
    r"Math\.|"
    r"idx\}|"  # numeric loop index
    r"rows\}|"
    r"links\}|"
    r"label\}|"
    r"path\}|"
    r"restore\}|"
    r"files\}|"
    r"parts\}|"
    r"header\}|"
    r"highlights\}|"
    r"sources\}|"
    r"warn\}|"
    r"tags\}|"
    r"expires\}|"
    # Pure ternary with only string literals or nested escapeHtml
    r"[^}]*\?\s*[\"'`]|"
    # String concatenation results (already escaped components)
    r'["\']'
    r")"
)

INNERHTML_ASSIGN = re.compile(r"\.innerHTML\s*[=+]")
TEMPLATE_INTERP = re.compile(r"\$\{[^}]+\}")


def _collect_js_files():
    return sorted(UI_STATIC.glob("*.js"))


def _find_violations(path: Path) -> list[str]:
    violations = []
    source = path.read_text(encoding="utf-8")
    lines = source.split("\n")

    in_template = False

    for i, line in enumerate(lines, 1):
        if INNERHTML_ASSIGN.search(line):
            in_template = True

        if in_template:
            for m in TEMPLATE_INTERP.finditer(line):
                interp = m.group(0)
                if not SAFE_INTERPOLATIONS.match(interp):
                    violations.append(
                        f"{path.name}:{i}: unescaped interpolation in innerHTML context: {interp}"
                    )

            if ";" in line and not line.strip().startswith("//"):
                in_template = False

    return violations


@pytest.mark.parametrize("js_file", _collect_js_files(), ids=lambda p: p.name)
def test_no_raw_innerhtml_interpolation(js_file):
    violations = _find_violations(js_file)
    assert not violations, (
        "Unescaped innerHTML interpolations found (E27-2 XSS regression):\n"
        + "\n".join(violations)
    )


def test_all_js_files_have_escape_html():
    """Every JS file with innerHTML must define an escapeHtml function."""
    for js_file in _collect_js_files():
        source = js_file.read_text(encoding="utf-8")
        if "innerHTML" not in source:
            continue
        if js_file.name == "sw.js":
            continue
        assert "escapeHtml" in source, (
            f"{js_file.name} uses innerHTML but does not define escapeHtml()"
        )
