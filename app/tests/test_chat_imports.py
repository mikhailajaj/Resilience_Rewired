"""Design rules D1-D6 (docs/architecture/j4_chat.md section 2), checked on import statements only."""
import ast
import sys
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[1]
NETWORK = {"requests", "httpx", "urllib", "http", "aiohttp", "socket", "anthropic", "openai"}
D1_FILES = ("app/ui/text.py", "app/ui/cheatsheet.py")
D5_ALLOWED = {"app/app_pages/assistant.py", "app/streamlit_app.py"}


def imports(source, rel):
    """Absolute module names imported by a file; relative imports resolve against its package."""
    pkg = rel.removesuffix(".py").split("/")[:-1]
    found = []
    for n in ast.walk(ast.parse(source)):
        if isinstance(n, ast.Import):
            found += [(a.name, n.lineno) for a in n.names]
        elif isinstance(n, ast.ImportFrom):
            if n.level:
                base = pkg[:len(pkg) - (n.level - 1)]
                found.append((".".join(base + ([n.module] if n.module else [])), n.lineno))
            else:
                found.append((n.module, n.lineno))
                found += [(f"{n.module}.{a.name}", n.lineno) for a in n.names]
    return found


def is_mod(name, *roots):
    return any(name == r or name.startswith(r + ".") for r in roots)


def d1(rel, source):
    if rel.startswith(("app/assistant/", "app/engine/")) or rel in D1_FILES:
        return [f"{rel}:{ln} imports {m}" for m, ln in imports(source, rel) if is_mod(m, "streamlit")]
    return []


def d2(rel, source):
    """Tests may import socket only to block it (test_chat_flow patches socket.socket to raise)."""
    allowed = {"socket"} if rel.startswith("app/tests/") else set()
    return [f"{rel}:{ln} imports {m}" for m, ln in imports(source, rel) if m.split(".")[0] in NETWORK - allowed]


def d3(rel, source):
    if not rel.startswith("app/assistant/"):
        return []
    bad = []
    for m, ln in imports(source, rel):
        top = m.split(".")[0]
        if top in sys.stdlib_module_names or is_mod(m, "app.engine", "app.assistant", "app.ui.text"):
            continue
        if m in ("app", "app.ui"):       # the parent of an allowed from-import, e.g. `from app.ui import text`
            continue
        bad.append(f"{rel}:{ln} imports {m}")
    return bad


def d4(rel, source):
    if rel.startswith("app/engine/"):
        return [f"{rel}:{ln} imports {m}" for m, ln in imports(source, rel) if is_mod(m, "app.assistant", "app.ui")]
    return []


def d5(rel, source):
    if rel.startswith(("app/tests/", "app/assistant/")) or rel in D5_ALLOWED:
        return []
    return [f"{rel}:{ln} imports {m}" for m, ln in imports(source, rel) if is_mod(m, "app.assistant")]


def d5_nav(rel, source):
    if rel != "app/streamlit_app.py":
        return []
    return [f"{rel}:{ln} imports {m}" for m, ln in imports(source, rel) if is_mod(m, "app.assistant") and m != "app.assistant.chat_text"
            and m != "app.assistant" and not m.startswith("app.assistant.chat_text.")]


def d6(rel, source):
    return [f"{rel}:{ln} imports {m}" for m, ln in imports(source, rel)
            if is_mod(m, "app.app_pages", "app_pages") or m.endswith("shock_and_plan")]


E1_ALLOWED = {"data", "errors", "formulas", "profile", "shock"}
E2_ALLOWED = {"rates", "plan", "shock", "profile", "formulas", "errors"}
E5_ALLOWED = {"data", "response", "profile", "shock", "plan"}
E3_FILES = ("app/ui/plan_text.py", "app/ui/findings_view.py")


def engine_deps(rel, source):
    """(engine module, line) for each import of a sibling inside app/engine; the package itself counts as `__init__`."""
    out = []
    for m, ln in imports(source, rel):
        if is_mod(m, "app.engine"):
            parts = m.split(".")
            out.append((parts[2] if len(parts) > 2 else "__init__", ln))
    return out


def only(rel, source, name, allowed):
    if rel != f"app/engine/{name}.py":
        return []
    return [f"{rel}:{ln} imports {sub}" for sub, ln in engine_deps(rel, source) if sub not in allowed]


def e1(rel, source):
    return only(rel, source, "rates", E1_ALLOWED)


def e2(rel, source):
    if rel.startswith("app/engine/") and rel != "app/engine/__init__.py":
        bad = [f"{rel}:{ln} imports goals" for sub, ln in engine_deps(rel, source) if sub == "goals"]
    else:
        bad = []
    return bad + only(rel, source, "goals", E2_ALLOWED)


def e3(rel, source):
    return [f"{rel}:{ln} imports {m}" for m, ln in imports(source, rel) if is_mod(m, "streamlit")] if rel in E3_FILES else []


def e5(rel, source):
    bad = only(rel, source, "findings", E5_ALLOWED)
    if rel.startswith("app/engine/") and rel not in ("app/engine/__init__.py", "app/engine/findings.py"):
        bad += [f"{rel}:{ln} imports findings" for sub, ln in engine_deps(rel, source) if sub == "findings"]
    return bad


def files():
    return [(p.relative_to(APP.parent).as_posix(), p.read_text()) for p in sorted(APP.rglob("*.py")) if "__pycache__" not in p.parts]


RULES = {"D1": d1, "D2": d2, "D3": d3, "D4": d4, "D5": lambda r, s: d5(r, s) + d5_nav(r, s), "D6": d6, "E1": e1, "E2": e2, "E3": e3, "E5": e5}


@pytest.mark.parametrize("rule", RULES)
def test_chat_import_rule_holds(rule):
    problems = [p for rel, src in files() for p in RULES[rule](rel, src)]
    assert not problems, problems


def test_chat_scan_sees_the_tree():
    rels = {r for r, _ in files()}
    assert {"app/assistant/state.py", "app/engine/shock.py", "app/ui/text.py", "app/app_pages/shock_and_plan.py"} <= rels


PLANTED = [
    ("D1", "app/assistant/x.py", "import streamlit as st"),
    ("D1", "app/engine/x.py", "from streamlit import cache_data"),
    ("D1", "app/ui/text.py", "import streamlit"),
    ("D1", "app/ui/cheatsheet.py", "from streamlit.runtime import x"),
    ("D2", "app/ui/x.py", "import requests"),
    ("D2", "app/engine/x.py", "import urllib.request"),
    ("D2", "app/tests/x.py", "from http import client"),
    ("D2", "app/assistant/x.py", "from socket import socket"),
    ("D2", "app/tests/x.py", "import requests"),
    ("D2", "app/assistant/x.py", "import anthropic"),
    ("D2", "app/ui/x.py", "import openai, httpx"),
    ("D3", "app/assistant/x.py", "import pandas"),
    ("D3", "app/assistant/x.py", "from app.ui.shared import md"),
    ("D3", "app/assistant/x.py", "from app.app_pages import shock_and_plan"),
    ("D4", "app/engine/x.py", "from app.assistant import state"),
    ("D4", "app/engine/x.py", "import app.ui.text"),
    ("D5", "app/ui/x.py", "from app.assistant import flow"),
    ("D5", "app/app_pages/customer_profiling.py", "import app.assistant.flow"),
    ("D5", "app/streamlit_app.py", "from app.assistant.flow import step"),
    ("D6", "app/assistant/x.py", "import app.app_pages.shock_and_plan"),
    ("D6", "app/app_pages/assistant.py", "from app.app_pages import shock_and_plan"),
    ("D6", "app/tests/x.py", "from app_pages.shock_and_plan import DEFAULTS"),
    ("E1", "app/engine/rates.py", "from .plan import make_plan"),
    ("E1", "app/engine/rates.py", "from .goals import PlanDesign"),
    ("E2", "app/engine/plan.py", "from .goals import PlanDesign"),
    ("E2", "app/engine/rates.py", "from .goals import PlanDesign"),
    ("E2", "app/engine/goals.py", "from .findings import biggest_finding"),
    ("E2", "app/engine/goals.py", "from .response import spending_response"),
    ("E3", "app/ui/plan_text.py", "import streamlit as st"),
    ("E3", "app/ui/findings_view.py", "from streamlit import cache_data"),
    ("E5", "app/engine/findings.py", "from .goals import PlanDesign"),
    ("E5", "app/engine/findings.py", "from .rates import saving_rates"),
    ("E5", "app/engine/plan.py", "from .findings import account_findings"),
]


@pytest.mark.parametrize("rule,rel,source", PLANTED)
def test_chat_import_rule_flags_planted_violation(rule, rel, source):
    assert RULES[rule](rel, source)


@pytest.mark.parametrize("rule,rel,source", [
    ("D1", "app/ui/shared.py", "import streamlit"),
    ("D3", "app/assistant/x.py", "from app.ui import text\nfrom .state import X\nimport math\nfrom app.engine.shock import MAX_MONTHS"),
    ("D5", "app/streamlit_app.py", "from app.assistant.chat_text import T"),
    ("D5", "app/app_pages/assistant.py", "from app.assistant import flow"),
    ("D5", "app/tests/x.py", "from app.assistant import flow"),
    ("D4", "app/engine/x.py", "from .shock import Shock"),
])
def test_chat_import_rule_allows_legal_import(rule, rel, source):
    assert not RULES[rule](rel, source)


@pytest.mark.parametrize("rule,rel,source", [
    ("E1", "app/engine/rates.py", "from .data import get_dataset\nfrom .profile import get_profile\nfrom .shock import MAX_MONTHS\nfrom .formulas import money\nfrom .errors import X"),
    ("E2", "app/engine/__init__.py", "from .goals import PlanDesign"),
    ("E2", "app/engine/goals.py", "from .rates import saving_rates\nfrom .plan import make_plan\nfrom .shock import Shock"),
    ("E3", "app/ui/shared.py", "import streamlit"),
    ("E5", "app/engine/findings.py", "from .data import x\nfrom .response import y\nfrom .plan import make_plan"),
    ("E5", "app/engine/__init__.py", "from .findings import account_findings"),
])
def test_engine_import_rule_allows_legal_import(rule, rel, source):
    assert not RULES[rule](rel, source)
