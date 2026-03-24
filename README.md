# Golf Coach R50

AI-drevet golftrener for **Garmin Approach R50** launch monitor. Appen henter slagdata fra Garmin Connect, analyserer dem med Claude AI, og gir deg praktiske coaching-tips i sanntid.

## Funksjoner

- **Sanntids slaganalyse**: Automatisk polling av nye slag fra Garmin Connect
- **AI Coaching**: Claude analyserer hvert slag og gir 1-3 handlingsrettede tips
- **Tilpassbart nivå**: Nybegynner, middels eller avansert — tipsene tilpasses ditt nivå
- **Mønstergjenkjenning**: Identifiserer slice/hook-tendenser, inkonsistens og trøtthet
- **Trendgrafer**: Visualiser carry, smash factor og spin over tid
- **Øktoppsummering**: Dyp analyse av hele treningsøkten med øvelsesforslag

## Arkitektur

```
Garmin Connect ← python-garminconnect → FastAPI Backend → Claude API
                                              ↓
                                         WebSocket
                                              ↓
                                    React Frontend (dashboard)
```

## Kom i gang

### Forutsetninger

- Python 3.12+
- Node.js 20+
- Garmin Connect-konto med R50-data
- Anthropic API-nøkkel

### 1. Backend

```bash
cd backend
cp .env.example .env
# Rediger .env med dine Garmin- og Anthropic-nøkler

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

uvicorn app.main:app --reload
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Åpne http://localhost:5173 i nettleseren.

### 3. Med Docker

```bash
cp backend/.env.example backend/.env
# Rediger backend/.env

docker compose up --build
```

Åpne http://localhost:5173 i nettleseren.

## Miljøvariabler

| Variabel | Beskrivelse |
|----------|-------------|
| `GARMIN_EMAIL` | Garmin Connect e-post |
| `GARMIN_PASSWORD` | Garmin Connect passord |
| `ANTHROPIC_API_KEY` | Din Anthropic API-nøkkel |
| `POLLING_INTERVAL_SECONDS` | Hvor ofte å sjekke for nye slag (standard: 30) |
| `DATABASE_PATH` | Sti til SQLite-database (standard: golf_coach.db) |

## Datapunkter fra R50

Appen analyserer disse datapunktene fra hvert slag:

| Metric | Beskrivelse |
|--------|-------------|
| Ball Speed | Ballhastighet etter treff |
| Launch Angle | Launsjvinkel |
| Spin Rate | Spin i rpm |
| Spin Axis | Spinaksens vinkel |
| Club Head Speed | Klubbhodehastighet |
| Club Face Angle | Klubbflatens vinkel ved treff |
| Club Path | Klubbbanens retning |
| Angle of Attack | Angrepsvinkel |
| Smash Factor | Energioverføringseffektivitet |
| Carry Distance | Carry-avstand |
| Total Distance | Total avstand |
| Apex Height | Høyeste punkt |
| Total Deviation | Sideveis avvik |

## Tech Stack

- **Backend**: Python, FastAPI, python-garminconnect, Anthropic SDK, SQLite
- **Frontend**: React, TypeScript, Vite, Recharts
- **AI**: Claude (Sonnet for per-slag, Opus for øktoppsummering)
- **Deployment**: Docker Compose
