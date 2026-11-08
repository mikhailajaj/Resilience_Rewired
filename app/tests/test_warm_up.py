"""Start-up cost (ADR 0009 decisions 2 and 3): warm_up within 15 s, cache hits under 50 ms, account_findings not computed."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = """
import json, time
t = time.perf_counter()
from app.engine import warm_up, biggest_finding, spending_response
from app.engine.findings import account_findings
warm_up()
warm = time.perf_counter() - t
t = time.perf_counter(); biggest_finding(); finding = time.perf_counter() - t
t = time.perf_counter(); spending_response(); response = time.perf_counter() - t
print(json.dumps(dict(warm=warm, finding=finding, response=response, size=account_findings.cache_info().currsize)))
"""


def test_warm_up_budget_cache_hits_and_account_findings_not_computed():
    out = subprocess.run([sys.executable, "-c", SCRIPT], cwd=ROOT, capture_output=True, text=True, timeout=120, check=True).stdout
    import json
    m = json.loads(out.strip().splitlines()[-1])
    print(m)
    assert m["warm"] < 15
    assert m["finding"] < 0.05 and m["response"] < 0.05
    assert m["size"] == 0
