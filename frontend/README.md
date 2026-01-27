# ProjectSeagull Frontend

React-based simulation dashboard for ProjectSeagull backtesting platform.

## Prerequisites

- Node.js 18+ and npm
- Backend server running on port 8000

## Setup

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at http://localhost:5173

## Features

### Configuration Management
- **Jobs Tab**: Create and manage simulation jobs (agent + test pairs)
- **Tests Tab**: Define test configurations (dates, trials, trading days)
- **Signals Tab**: Register data signals (Massive API / Sharadar SF1)
- **Agents Tab**: View, clone, and manage trading agents

### Simulation Dashboard
- Real-time candlestick charts (TradingView Lightweight Charts)
- Equity curve visualization (Recharts)
- Trade markers on price chart
- Job navigation (left/right switching between concurrent jobs)
- Live P&L and metrics display

## Tech Stack

- **React 18** with TypeScript
- **Vite** for build tooling
- **Tailwind CSS** for styling
- **Zustand** for state management
- **TradingView Lightweight Charts** for candlesticks
- **Recharts** for line charts
- **Lucide React** for icons

## Project Structure

```
src/
├── api/
│   └── client.ts        # REST API client
├── components/
│   ├── Charts/          # Chart components
│   ├── ConfigPanel/     # Config management tabs
│   ├── Dashboard/       # Simulation dashboard
│   └── Navigation/      # Job list sidebar
├── hooks/
│   └── useWebSocket.ts  # WebSocket connection hook
├── stores/
│   └── simulationStore.ts  # Zustand store
├── types/
│   └── index.ts         # TypeScript types
├── App.tsx
├── main.tsx
└── index.css
```
