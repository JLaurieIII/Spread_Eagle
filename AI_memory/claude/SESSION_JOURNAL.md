# SESSION JOURNAL

Running log of development sessions. Most recent first.

---

## 2026-01-01 (Evening Session)

**Duration:** ~3 hours
**Focus:** dbt setup + ML predictions + Frontend

### What Happened

1. **Project Cleanup**
   - User deleted old dbt folders to start fresh
   - Moved `ml/` folder into `spread_eagle/` package for cleaner imports

2. **Python Environment**
   - Discovered Python 3.14 doesn't support dbt (too new)
   - Installed Python 3.12 via `winget install Python.Python.3.12`
   - Created fresh venv with 3.12
   - Installed: dbt-postgres, xgboost, scikit-learn, pandas, python-dotenv

3. **dbt Deep Dive**
   - Initialized `dbt_transform/` project from scratch
   - Explained layer cake: staging → intermediate → marts
   - Created custom schema macro for clean names (`staging_cfb` not `dbt_staging_cfb`)
   - Built 11 models total across 3 layers
   - Created `DBT_LEARNING_GUIDE.md` for reference

4. **The 10 Views Architecture**
   - User provided detailed spec for 10 analytical views
   - Implemented 7 of them (staging + intermediate + 5 marts)
   - Foundation model: `int_cfb__game_team_lines` (the critical unpivot)

5. **ML Predictions**
   - Created `predict_bowl_games.py` with XGBoost
   - Trains on historical completed games
   - Predicts upcoming games from `fct_cfb__upcoming_predictions`
   - Generated picks for 12 bowl games
   - Created `ML_LEARNING_GUIDE.md` for reference

6. **Frontend**
   - Created `/predictions` page with picks display
   - Created `/api/predictions` route (static data for now)
   - Existing main page has cool flag wave animation

7. **AI Memory System**
   - Created `AI_memory/claude/` folder structure
   - This journal, plus overview docs for future sessions

### Key Decisions Made

- **Schema naming:** `staging_cfb`, `intermediate_cfb`, `marts_cfb` (by layer + sport)
- **Materialization:** Staging as views, everything else as tables
- **Model approach:** XGBoost classifier, chronological train/test split
- **Feature set:** Rolling ATS margins, cover rates, deltas (no advanced stats)

### User Insights

- Learning-focused, wants to understand not just copy
- Building portfolio project
- Prefers clean code organization
- Interested in both CFB and CBB

### Issues Encountered

1. Python 3.14 incompatible with dbt (mashumaro library)
2. Legacy `py.exe` conflicting with new Python installer
3. Heredoc escaping issues in bash (used Write tool instead)
4. Correlated subqueries slow in margin_sequence model

### Left Off At

- Frontend running but predictions page formatting needs work
- 12 bowl game predictions generated
- User wanted to create AI memory system (done)

---

## Template for Future Entries

```markdown
## YYYY-MM-DD (Morning/Afternoon/Evening)

**Duration:** X hours
**Focus:** [main topic]

### What Happened
1. ...
2. ...

### Key Decisions Made
- ...

### Issues Encountered
- ...

### Left Off At
- ...
```
