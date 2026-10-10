# Habit Tracker 🌸

An independent Streamlit habit tracker inspired by the pink dashboard reference.

## Includes
- Pink floral-inspired header and clock cards
- Daily task list (default task: Watch BiggBoss)
- Default habits from the latest supplied code:
  - Waking Up at 7 AM
  - Drinking 3 Litres of Water
  - 8 Hours of Sleep
- Daily checkbox grid
- Weekly progress summary and daily consistency
- Monthly progress summary and calendar
- Habit-by-habit weekly/monthly rates
- SQLite persistence

## Run locally
```bash
uv venv
uv pip install -r requirements.txt
uv run streamlit run app.py
```

The app creates `data/habit_tracker.db` automatically. Habit and completion records are stored there.

## Deploy
Push this folder to a GitHub repository, then deploy `app.py` using Streamlit Community Cloud.
