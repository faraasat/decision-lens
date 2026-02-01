# DecisionLens AI Assistant Coach

DecisionLens is an AI assistant coach for League of Legends and VALORANT. It ingests GRID match data, normalizes timelines, and generates coach-ready insights: macro swings, micro mistakes, win-probability shifts, and explainable “what-if” scenarios. The dashboard is a live, scifi-styled coaching view built for fast review and decision support.

## What it does

- **Live & post-match analysis** using GRID series timelines and stats.
- **Win probability telemetry** powered by XGBoost with SHAP explanations.
- **Macro inflection detection** for turning points and objective swings.
- **Micro performance signals** (isolated deaths, efficiency, economy/vision).
- **Counterfactual review** to quantify alternate decisions.

## Tech stack

- **Backend:** FastAPI + pandas/numpy, XGBoost, SHAP
- **Frontend:** Next.js (App Router), Recharts, Tailwind CSS
- **Data:** GRID Central Data + File Download APIs

## Run the project

### Prerequisites

- Python 3.9+
- Node.js 18+
- Yarn or npm

### 1) Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Add your GRID API key to `.env`:

```
GRID_API_KEY=YOUR_KEY
```

### Monorepo shortcut

From the repo root:

```bash
yarn
yarn dev
```

## Notes

- Without a valid `GRID_API_KEY`, live series lists and real timelines will not load.
- Live mode can fall back to simulated data when a series doesn’t expose full timeline frames.

## References

- [GRID GraphQL Playground](https://docs.grid.gg/public/documentation/graphql-playground)
- [GRID API Overview](https://docs.grid.gg/public/documentation/api-documentation/getting-started/overview)
