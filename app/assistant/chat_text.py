"""The chat's connecting lines (T.*), verbatim from docs/design/ux/copy.md section 10. Result sentences come from app/ui/text.py, not here.

Strings marked NEW-COPY-n are drafted in docs/architecture/j4_chat.md section 9 and wait for the copy owner.
"""
from app.engine.shock import MAX_MONTHS


class T:
    page = "Chat"
    no_customer = "Load a customer in the box above, then I can run a twist for them."
    greet = "Hi. I have customer {id} loaded."
    range = "Data from {first_month} to {last_month} ({n_months} months)."
    pick = "Which twist? Pick one, or type the card."
    b_job = "Job loss on EI"
    b_bills = "Bills go up"
    b_repair = "Surprise repair"
    b_mix = "Mix"
    b_type = "Type it"
    ask_keep = "How much of their usual income does EI keep? The README uses 55%."
    ask_months = "For how long?"
    ask_bills = "How much do household bills go up?"
    ask_repair = "How much does the repair cost?"
    not_number = "Type a number, like 55."
    out_of_range = "{value} is outside what the engine takes: {size} must be {range}. Pick a size or type another."
    engine_refused = "The engine didn't accept {field}. Pick that size again."
    engine_call = "⚙ engine call: `{call}`"
    change_line = "Runway {R0} -> {R1}. Monthly gap {g0} -> {g1}."          # NEW-COPY-6: copy has ${g0}; text.money already adds the $
    ours = "(ours)"
    confirm = "I read this as: {plain}. Run it?"
    b_run = "Run it"
    b_buttons = "No, use buttons"
    partial = "I read: {plain}. I still need {size}."
    unsure = "I'm not sure how to read that, so I won't guess. Pick a twist instead."
    unsure_month = "I can't set a start month here. Use More options on the Shock and plan page."
    f_backup = "Show the backup plan"
    f_goal = "Show the goal plan"
    f_stack = "Add another shock"
    f_size = "Change the size"
    f_new = "New customer"
    f_send = "Send to the controls"
    pick_size = "Which size?"
    stack_replace = "This replaces the earlier {kind}: {old} -> {new}."
    new = "Type the new account number in the box at the top."
    send_ok = "Sent. The Shock and plan page now has these sizes."
    send_cant = "The controls can't hold {what}, so nothing was sent. The numbers above stand."
    download = "Download transcript"
    download_help = "The chat lasts until the page is closed, so download it to keep it."

    # Size buttons, from the flows section 4 state table.
    v_keep_55 = "55%"
    v_months_6 = "6 months"
    v_months_12 = "12 months"
    v_months_none = "Until it runs out"
    v_bills_15 = "+15%"
    v_repair_1 = "1 month of spending"
    b_dollars_month = "Dollars a month"
    b_dollar_amount = "Dollar amount"

    type_prompt = "Type the card in the box below."                       # NEW-COPY-1
    other = "Other"                                                       # NEW-COPY-5
    use = "Use"                                                           # NEW-COPY-5
    placeholder = "Type the twist card, or a size"                        # NEW-COPY-5
    ours_line = "{label}: {value} ({counterpart}) (ours)"                 # NEW-COPY-7
    cheatsheet = "How to type a twist card"                               # NEW-COPY-8

    # Other-box placeholders, per field (flows section 4; the ones flows doesn't name follow RU-22).
    hint_keep = "0 to 100"
    hint_months = f"1 to {MAX_MONTHS}"
    hint_pct = "0 or more"
    hint_dollars_month = "$ a month"
    hint_spending = "months of spending"
    hint_dollars = "$"

    # {plain}: the shock in words, parts joined by plain_join (NEW-COPY-2). {d} is text.money's value. The one-month forms are ours (NEW-COPY-9).
    plain_keep = "income kept at {n}%"
    plain_months = "for {n} months"
    plain_month_one = "for 1 month"
    plain_months_assumed = "for {n} months (assumed)"
    plain_open = "until it runs out"
    plain_no_income = ", then no income"
    plain_returns = ", then income returns"
    plain_bills = "bills up {n}%"
    plain_rent = "bills or rent up {d} a month"
    plain_repair_months = "a one-off cost of {n} months of spending"
    plain_repair_month_one = "a one-off cost of 1 month of spending"
    plain_repair_dollars = "a one-off cost of {d}"
    plain_join = "; "

    # T.send_cant {what} (NEW-COPY-3).
    cant_open = "a job loss with no end month"
    cant_returns = "income coming back"
    cant_bills = "bills up {n}%"
    cant_rent = "rent up {d} a month"
    cant_repair_months = "a one-off of {n} months of spending"
    cant_repair_dollars = "a one-off of {d}"
    cant_two = "two one-off costs"

    # T.stack_replace {kind} and the PickSize buttons (NEW-COPY-10, drafted here).
    kind_job = "job loss"
    kind_bills = "bills rise"
    kind_repair = "repair"
    size_button = "Change {size} ({shown})"
