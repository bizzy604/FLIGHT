# REA Flight Portal

An end-to-end flight booking portal integrating Verteil NDC APIs with a modern Next.js frontend and a Quart (async Flask) backend. The system emphasizes robust caching via Redis to deliver fast navigation and resilient booking flows even when client-side raw responses are not persisted.

## Project Overview

- End-to-end NDC flow: AirShopping → FlightPrice → SeatAvailability/ServiceList → OrderCreate
- Resilient cache-key strategy so booking is unblocked even if raw NDC price response is not present on the client
- Multi-layer caching with Redis (backend) and lightweight in-memory/session scoping on the client for UX hints
- Clear separation of concerns: Backend handles external APIs, caching and transformations; Frontend manages UX and orchestration

## Tech Stack

- Frontend: Next.js (App Router), TypeScript, TailwindCSS
- Backend: Python, Quart (async Flask), Hypercorn server
- Caching: Redis (Redis Cloud supported), unified cache services on backend
- Data: Prisma (Frontend DB connectivity if enabled), Axios/Fetch for HTTP
- Tooling: ESLint/Prettier, Jest/Playwright (optional), Pytest (backend), logging via console and Python logging

## Monorepo Structure

- Backend/ — Quart app, routes, services, Redis integration
- Frontend/ — Next.js app, pages, components, utils, API routes (proxy to backend)
- documentations/ — Architecture notes, setup guides, cache design and debugging guides

## Setup

1) Prerequisites
- Node.js 18+
- Python 3.10+
- Redis (local or Redis Cloud) — optional for dev, recommended

2) Environment Variables

Backend (examples):
- VERTEIL_API_BASE_URL
- VERTEIL_USERNAME, VERTEIL_PASSWORD
- VERTEIL_CLIENT_ID, VERTEIL_CLIENT_SECRET (if applicable)
- VERTEIL_OFFICE_ID, VERTEIL_THIRD_PARTY_ID (if applicable)
- VERTEIL_TOKEN_ENDPOINT (default /oauth2/token)
- REDIS_URL or REDIS_HOST/REDIS_PORT/REDIS_DB/REDIS_PASSWORD
- OAUTH2_TOKEN_EXPIRY_BUFFER (default 300)

Frontend (examples):
- NEXT_PUBLIC_API_BASE_URL (defaults to http://localhost:5000)
- NEXT_PUBLIC_FIXER_API_KEY / NEXT_PUBLIC_CURRENCYLAYER_API_KEY (optional currency rates)
- DATABASE_URL (if using Prisma features)

3) Install dependencies
- Backend: pip install -r Backend/requirements.txt
- Frontend: cd Frontend && npm install

4) Configure Redis
- You may run without Redis (backend will warn but continue). For Redis Cloud, set REDIS_URL accordingly.
- See documentations/REDIS_DEPLOYMENT_GUIDE.md and documentations/REDIS_CLOUD_SETUP.md for options.

## Running Locally

- Start backend:
  - cd Backend
  - set environment variables (see above)
  - python app.py (runs Hypercorn via if __name__ == '__main__')
- Start frontend:
  - cd Frontend
  - set NEXT_PUBLIC_API_BASE_URL to backend URL
  - npm run dev

Open http://localhost:3000 for the frontend, backend listens on http://localhost:5000 by default.

## Usage Examples

Core flow endpoints (backend):
- POST /api/verteil/air-shopping
- POST /api/verteil/flight-price
- POST /api/verteil/seat-availability
- POST /api/verteil/service-list
- POST /api/verteil/order-create

Frontend utils:
- utils/simple-api-manager.ts orchestrates proactive loading of seat/service and ensures cache keys exist before booking
- utils/api-client.ts provides ready-to-use methods for getFlightPrice and createBooking with normalized responses

Behavioral guarantees:
- Payment flow proceeds even when raw flight price response is absent on the client; cache keys are derived from metadata or IDs
- Proactive loaders persist backend storage_key values, which are passed to OrderCreate to avoid recomputation

## Testing

- Backend: pytest from Backend directory
- Frontend: npm test (configure as needed)
- Cache health: Backend provides cache health/debug routes (see Backend/routes)

## Deployment

- Backend: Deploy Quart app on a container platform or VM; configure environment variables. Hypercorn is used as ASGI server.
- Redis: Prefer Redis Cloud in production; set REDIS_URL as a secret.
- Frontend: Deploy Next.js app (Vercel/Netlify/Render). Ensure NEXT_PUBLIC_API_BASE_URL points to the backend.

## Contributing

1. Fork and create a feature branch
2. Keep changes scoped and documented
3. Add/adjust tests where relevant
4. Ensure lint/test pass for both Frontend and Backend
5. Open a PR with a clear description

## License

MIT License — see LICENSE file if present. If absent, the project is provided under MIT terms as stated here.
