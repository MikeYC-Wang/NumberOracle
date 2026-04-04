# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

NumberOracle is a Taiwan lottery data analysis and prediction platform. It supports three lottery types: 今彩539 (Daily Cash 5/39), 大樂透 (Lotto 6/49), and 威力彩 (SuperLotto 6/38). The project uses historical data statistics and probability calculations to provide analysis tools and number selection predictions.

## Commands

### Backend (from `backend/` directory)
```bash
python manage.py runserver 8001          # Start dev server on port 8001
python manage.py migrate                 # Apply database migrations
python manage.py seed_games              # Initialize 3 lottery game records
python manage.py fetch_draws --game daily_cash --year 2025  # Fetch historical data
python manage.py update_latest           # Fetch current+previous month data (for cron)
python manage.py makemigrations lottery   # Generate migrations after model changes
```

### Frontend (from `frontend/` directory)
```bash
npm run dev        # Vite dev server (port 5173)
npm run build      # vue-tsc type check + Vite production build
npm run preview    # Preview production build
npx vue-tsc --noEmit   # TypeScript check only (no build)
```

### Important: always run frontend commands from `frontend/` directory. Running `vue-tsc` from `backend/` will invoke the wrong TypeScript compiler.

## Architecture

### Tech Stack
- **Backend:** Django 6 + Django REST Framework + PostgreSQL
- **Frontend:** Vue 3 (Composition API) + TypeScript + Vite 8 + Pinia + ECharts
- **Auth:** DRF Token Authentication
- **Database:** PostgreSQL with `INTEGER[]` ArrayField + GIN indexes for statistical queries

### Backend Structure (`backend/`)
- `core/` -- Django project config (settings, root urls)
- `lottery/` -- Main app: models (LotteryGame, DrawResult), DRF ViewSets, serializers, management commands
- `accounts/` -- Auth app: register/login/logout/profile using DRF Token auth

### API Layout
- `api/v1/games/` -- LotteryGameViewSet (ReadOnly, lookup_field='code')
- `api/v1/draws/` -- DrawResultViewSet with many `@action` endpoints:
  - `hot_cold`, `missing_values`, `trend`, `summary`, `refresh` (POST, 60s rate limit)
  - `consecutive_tail`, `zone_distribution`, `odd_even_size`, `ac_value`, `pair_frequency`
  - `road_map`, `check_numbers` (POST)
- `api/v1/auth/` -- register, login, logout, profile

### Frontend Structure (`frontend/src/`)
- `stores/` -- Pinia: `authStore` (token in localStorage), `lotteryStore` (games), `analysisStore` (all stats data + selectedRecent)
- `views/` -- Dashboard, 3 analysis pages (DailyCash/Lotto649/SuperLotto share same layout), PredictionView (5 strategies + animations), CheckNumbersView, Login/Register
- `components/charts/` -- ECharts wrappers, each with `.chart-scroll-wrapper` for mobile horizontal scroll
- `components/common/` -- LotteryBall, StatCard, DataTable, PeriodSelector
- `composables/useChartOptions.ts` -- Shared ECharts option generators with color interpolation
- `types/lottery.ts` -- TypeScript interfaces for API responses

### Key Data Flow
1. Taiwan Lottery API → `fetch_draws` command → PostgreSQL `draw_results` table (INTEGER[] arrays)
2. DRF ViewSet `@action` endpoints → `unnest` arrays / iterate in Python → JSON statistics
3. Frontend Pinia stores → fetch API → reactive refs → ECharts/components

### Environment (.env at project root)
- `VITE_API_BASE_URL` -- Frontend reads via Vite's envDir config
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` -- Backend reads via python-dotenv

## Design Constraints

- **No emojis anywhere** in the UI. Icons use FontAwesome exclusively.
- **Color palette:** Background #F4F1DE, Primary #E9C46A, Secondary #2A9D8F, Accent #E76F51
- **All h1/h2/h3 with icons** must use `display: flex; align-items: center; gap` for vertical centering
- **Chart components** must wrap in `.chart-scroll-wrapper` with `overflow-x: auto; max-width: 100%` for mobile
- **CSS Grid children** containing charts need `min-width: 0` to prevent overflow on mobile
- **Frontend imports** use relative paths (e.g., `../../types/lottery`), not `@/` alias (not configured in Vite)
- **Communication language:** Traditional Chinese (zh-Hant) for all UI text
- **Git operations** are manual -- never auto-commit or push

## Lottery Game Codes
| Code | Name | Main | Special |
|------|------|------|---------|
| `daily_cash` | 今彩539 | 5 from 39 | None |
| `lotto649` | 大樂透 | 6 from 49 | 1 from 49 |
| `super_lotto` | 威力彩 | 6 from 38 | 1 from 8 |
