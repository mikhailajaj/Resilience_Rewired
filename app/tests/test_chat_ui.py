"""Chat page tests through AppTest. Group A needs only the page and the stubs; group B needs the real assistant modules (AC-1, 2, 7, 8, 9)."""
from streamlit.testing.v1 import AppTest

from app.assistant import flow, transcript
from app.assistant.chat_text import T
from app.assistant.state import ConfirmPicked, FollowUpPicked, TwistPicked, ValuePicked
from app.tests.test_ui import APP, page, show

CHAT = "app_pages/assistant.py"
SHOCK = "app_pages/shock_and_plan.py"


def open_chat(account=None):
    at = AppTest.from_file(APP, default_timeout=60).run()
    assert not at.exception
    if account is not None:
        show(at, account)
    at.switch_page(CHAT).run()
    assert not at.exception
    return at


def click(at, event_type, **fields):
    """Click the live button whose event has this type and these field values."""
    state = at.session_state["chat"]
    for option in flow.live(state).options:
        event = option.event
        if isinstance(event, event_type) and all(getattr(event, k) == v for k, v in fields.items()):
            at.button(key=f"chat_{state.turn}_{option.key}").click().run()
            assert not at.exception
            return at
    raise AssertionError(f"no live button for {event_type.__name__} {fields}")


def chat_keys(at):
    return [b.key for b in at.button if b.key and b.key.startswith("chat_") and b.key != "chat_download"]


def run_job(at, months=6):
    click(at, TwistPicked, twist="job")
    click(at, ValuePicked, field="keep_pct", value=55)
    return click(at, ValuePicked, field="months", value=months)


# --- group A: wiring ---

def test_chat_page_is_in_navigation_and_opens():
    at = open_chat()
    assert any(T.page in str(s.value) for s in at.subheader)


def test_no_customer_shows_the_prompt_and_disables_input():
    at = open_chat()
    assert T.no_customer in page(at)
    assert at.chat_input(key="chat_text").disabled


def test_greeting_names_the_customer_and_offers_the_twists():
    at = open_chat(20111)
    turn = at.session_state["chat"].turn
    assert "20111" in page(at)
    assert not at.chat_input(key="chat_text").disabled
    for slug in ("job", "bills", "repair"):
        at.button(key=f"chat_{turn}_{slug}")


def test_AC7_only_the_latest_buttons_exist_after_each_click():
    at = open_chat(20111)
    click(at, TwistPicked, twist="job")
    turn = at.session_state["chat"].turn
    keys = chat_keys(at)
    assert keys and all(k.startswith(f"chat_{turn}_") for k in keys)


def test_download_button_is_present_with_the_transcript_file_name():
    at = open_chat(20111)
    assert transcript.file_name(at.session_state["chat"]) == "chat_transcript_20111.md"
    buttons = at.get("download_button")
    assert buttons and buttons[0].proto.label == T.download and not buttons[0].proto.disabled


def test_download_button_is_disabled_without_a_customer():
    at = open_chat()
    assert at.get("download_button")[0].proto.disabled


# --- group B: needs the real modules ---

def test_AC1_job_loss_by_clicks_gives_the_judges_numbers():
    at = open_chat(20111)
    run_job(at)
    body = page(at)
    assert "IncomeCut(0.55, 6)" in body
    assert "the money runs out in month 4, about 2.6 months short" in body
    assert "The judges' runway is 3.4 months." in body
    assert "Monthly gap $2,260 -> $5,113." in body


def test_AC2_chat_and_shock_page_agree_on_the_same_shock():
    at = open_chat(20111)
    run_job(at)
    at.switch_page(SHOCK).run()
    at.button(key="preset_Laid off, EI 55%").click().run()
    assert not at.exception
    assert "the money runs out in month 4, about 2.6 months short" in page(at)
    assert "Monthly gap  $2,260 -&gt; $5,113" in str([h.proto for h in at.get("html")])   # raw() escapes the arrow


def test_AC8_a_new_customer_starts_a_new_section_and_the_transcript_keeps_both():
    at = open_chat(20111)
    run_job(at)
    show(at, 20134)
    shown = "\n".join(line for m in at.session_state["chat"].messages for line in m.lines)   # the picker caption names 20111 as an example
    assert "20111" not in shown and "20134" in shown and "Customer 20134" in page(at)
    text = transcript.to_markdown(at.session_state["chat"])
    assert "## Customer 20111" in text and "## Customer 20134" in text
    assert text.index("## Customer 20111") < text.index("## Customer 20134")


def test_AC9_send_to_the_controls_opens_shock_and_plan_with_the_sizes():
    at = open_chat(20111)
    run_job(at)
    click(at, FollowUpPicked, action="send")
    assert at.number_input(key="n_income").value == 55
    assert "runs out in month 4" in page(at)


def test_AC9_open_ended_months_cannot_be_sent_and_the_page_stays_on_chat():
    at = open_chat(20111)
    run_job(at, months=None)
    click(at, FollowUpPicked, action="send")
    assert T.send_cant.format(what=T.cant_open) in page(at)
    assert not at.get("number_input") or not any(n.key == "n_income" for n in at.number_input)


def test_typed_card_waits_for_confirm_then_runs_with_the_bills_rise():
    at = open_chat(20111)
    at.chat_input(key="chat_text").set_value("laid off, EI 55% for 6 months and bills up 15%").run()
    assert not at.exception
    state = at.session_state["chat"]
    assert "I read this as:" in page(at)
    assert "⚙ engine call" not in page(at) and state.outputs == ()
    click(at, ConfirmPicked, run=True)
    body = page(at)
    assert "⚙ engine call" in body and "bills_increase_pct=15" in body
