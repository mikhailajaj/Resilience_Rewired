"""Submission and config checks (R2, R12, D9, D10, D13). Covers WP-D of the J5 build."""

from pathlib import Path

import pytest

TEST_COUNT = 1214

ROOT = Path(__file__).resolve().parents[2]
POST = (ROOT / "project_dev-post.md").read_text(encoding="utf-8")
README = (ROOT / "app" / "README.md").read_text(encoding="utf-8")
CTU = "https://relational.fel.cvut.cz/dataset/Financial"
EI = "https://www.canada.ca/en/services/benefits/ei/ei-regular-benefit/benefit-amount.html"


@pytest.mark.parametrize("heading", ["## Sources", "## Credits", "## Biggest finding"])
def test_r2_d10_headings(heading):
    assert heading in POST.splitlines()


@pytest.mark.parametrize("url", [CTU, EI])
def test_r2_d9_source_urls(url):
    assert url in POST


@pytest.mark.parametrize(
    "text",
    [
        "1,526",
        "22 more if the lender agrees",
        "1,548",
        "1,038 of 3,309",
        "four pages",
        "735",
        "493",
    ],
)
def test_r2_d13_wording(text):
    assert text in POST


def test_r2_no_stale_page_count():
    assert "three pages" not in POST.lower()
    assert "two pages" not in POST.lower()
    assert "829 tests" not in POST


def test_r2_credits_name_pkdd_and_government():
    credits = POST.split("## Credits", 1)[1].split("\n## ", 1)[0]
    assert "PKDD'99" in credits and CTU in credits
    assert "Government of Canada" in credits


def test_r2_test_count_matches_docs():
    assert TEST_COUNT > 0
    figure = f"{TEST_COUNT:,}"
    assert f"{figure} tests" in POST
    assert figure in README


def test_r2_readme_pages_and_command():
    assert "four-page" in README
    for page in ("Shock and plan", "Customer profiling", "Chat", "Findings"):
        assert page in README
    assert ".venv/bin/python -m pytest app/tests -q -p no:cacheprovider" in README


def test_r12_root_requirements_include_app_pins():
    lines = (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
    assert lines[0] == "-r app/requirements.txt"
    app_pins = {
        l.split("==")[0].strip().lower()
        for l in (ROOT / "app" / "requirements.txt").read_text().splitlines()
        if l.strip()
    }
    rest = {l.strip().lower() for l in lines[1:] if l.strip()}
    assert not (app_pins & rest)
    assert {"pytest", "jupyterlab"} <= rest


def test_r12_config_disables_usage_stats():
    config = (ROOT / "app" / ".streamlit" / "config.toml").read_text(encoding="utf-8")
    assert "[browser]" in config
    assert "gatherUsageStats = false" in config
