# DecisionLens AI Assistant Coach

An AI-powered assistant coach for League of Legends & Valorant, designed to provide real-time strategic insights and post-match analysis using GRID telemetry.

## Features

- **Win Probability Telemetry**: Real-time XGBoost-powered win probability forecasting based on gold, XP, and objectives.
- **Macro Inflection Detection**: Identifies critical game-turning moments and strategic shifts.
- **Micro Performance Analysis**: Detects player mistakes (e.g., isolated deaths) and calculates efficiency metrics (GPM, total gold).
- **Counterfactual "What-If" Engine**: Simulate alternate scenarios to quantify the impact of strategic decisions.
- **AI Strategic Overview**: LLM-synthesized summaries with priority action items for coaches.

## Getting Started

### Prerequisites

- Python 3.9+
- Node.js 18+
- Yarn or NPM

### Backend Setup

1. Navigate to `backend/`
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and add your GRID API Key (optional, defaults to mock data).
4. Start the server: `fastapi dev app/main.py`

### Frontend Setup

1. Navigate to `frontend/`
2. Install dependencies: `npm install` or `yarn install`
3. Start the dev server: `npm run dev` or `yarn dev`
4. Access the dashboard at `http://localhost:3000`

## Documentation & References

- [GRID GraphQL Documentation](https://docs.grid.gg/public/documentation/graphql-playground)
- [GRID API Getting Started](https://docs.grid.gg/public/documentation/api-documentation/getting-started/overview)
