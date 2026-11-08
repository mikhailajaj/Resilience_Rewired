# Resilience Rewired app

A four-page Streamlit app over the engine in `engine/`. The customer picker sits above the pages and keeps one customer across them.

- **Shock and plan:** type any `account_id`, apply a shock, and get a goal plan and a backup plan. Below them, the plan designer ("If you adjust") lets you change saving, loan end and the goal and see the date move.
- **Chat:** a guided conversation that runs a twist on the loaded customer, by buttons or a typed card.
- **Customer profiling:** everything on file for the customer, and [questions to ask the stakeholder](../docs/customer_profiling.md).
- **Findings:** what the data shows across all accounts, with the customer's own numbers beside it.

## Run it

Run from this folder, so Streamlit finds `.streamlit/config.toml`. The first load takes about 5 seconds while the data loads.

```bash
cd app
../.venv/bin/streamlit run streamlit_app.py
```

## Test it

Run from the `Tangerine` folder.

```bash
.venv/bin/python -m pytest app/tests -q -p no:cacheprovider
```

The suite collects 1,214 tests.

## Layout

| Path | What it holds |
| :-- | :-- |
| `streamlit_app.py` | Navigation, theme CSS, engine start-up and the customer picker |
| `app_pages/shock_and_plan.py` | Input state and layout, regions B to H from [`wireframes.md`](../docs/design/ux/wireframes.md) |
| `app_pages/customer_profiling.py` | The profile tabs and the questionnaire |
| `app_pages/findings.py` | The Findings page |
| `ui/plan_designer.py` | The plan designer section on Shock and plan |
| `app_pages/assistant.py` | The Chat page: draws the state from `assistant/flow.py`, sends clicks and typed lines back |
| `ui/shared.py` | Text helpers and the picker, used by both pages |
| `ui/profile_view.py` | The rows on the profiling page |
| `ui/questionnaire.py` | Which questions each customer gets, and the Markdown download |
| `ui/text.py` | Every sentence on screen, from [`copy.md`](../docs/design/ux/copy.md). No Streamlit, so tests cover every account |
| `ui/charts.py` | The two Details charts, from [`charts.md`](../docs/design/visual/charts.md) |
| `ui/style.py` | The injected CSS, from [`components.md`](../docs/design/visual/components.md) |
| `engine/` | All the numbers. See [`engine_contract.md`](../docs/engine_contract.md) |
| `static/` | Figtree font files, under the SIL Open Font License (`Figtree-OFL.txt`) |
