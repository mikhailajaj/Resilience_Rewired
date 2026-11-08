"""chat_text.T against docs/design/ux/copy.md section 10."""
import re
from pathlib import Path

from app.assistant.chat_text import T

COPY = Path(__file__).parents[2] / "docs" / "design" / "ux" / "copy.md"


def copy_rows():
    section = COPY.read_text().split("## 10. Chat (T)", 1)[1]
    rows = {}
    for line in section.splitlines():
        m = re.match(r"\| (T\.[^|]+?) \| (.+) \|$", line)
        if not m:
            continue
        keys = [k.strip()[2:] for k in m.group(1).split(", ")]
        texts = m.group(2).split(" · ") if len(keys) > 1 else [m.group(2)]
        assert len(keys) == len(texts), line
        rows.update(zip(keys, texts))
    return rows


def test_chat_copy_table_is_read():
    rows = copy_rows()
    assert len(rows) >= 39 and rows["b_job"] == "Job loss on EI" and rows["b_buttons"] == "No, use buttons"


def test_chat_text_matches_copy():
    for key, expected in copy_rows().items():
        assert hasattr(T, key), key
        if key == "change_line":
            expected = expected.replace("${", "{")
        assert getattr(T, key) == expected, key


def test_new_copy_3_and_10_and_17_wording_is_settled_in_copy_md():
    assert T.cant_open == "a job loss with no end month"
    assert T.size_button.format(size="income kept", shown="55%") == "Change income kept (55%)"
    assert T.plain_months_assumed.format(n=6) == "for 6 months (assumed)"
