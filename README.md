# Transformation Coaching

A full-stack web application for a personal coaching business with Garmin Connect integration for workout sharing between coaches and athletes.

## Features

- **Landing Page** — Public-facing page with mission statement, services overview, and contact form
- **Role-Based Access** — Admin, Coach, and Athlete dashboards with appropriate permissions
- **Garmin Connect Integration** — Coaches export workouts from their Garmin account and share them with athletes, who can import them directly to their own Garmin devices
- **User Management** — Admin dashboard for creating, editing, and deactivating users
- **Secure Authentication** — JWT tokens with refresh, Google OAuth support, encrypted credential storage
- **Mobile-Friendly** — Responsive design using TailwindCSS

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, TypeScript, TailwindCSS, React Router, Axios |
| Backend | FastAPI, Python 3.11, SQLAlchemy (async), Pydantic |
| Database | PostgreSQL 15 (asyncpg) |
| Garmin API | python-garminconnect (via garth OAuth) |
| Auth | JWT (python-jose), bcrypt, Google OAuth |
| Encryption | Fernet (AES-256) for Garmin credentials |
| Containerization | Docker, Docker Compose |
| Testing | pytest (backend), Jest (frontend) |

## Project Structure

```
transformation-coaching/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI route handlers
│   │   ├── core/         # Config, database, security
│   │   ├── models/       # SQLAlchemy models
│   │   └── services/     # Garmin service layer
│   ├── alembic/          # Database migrations
│   ├── tests/            # pytest test suite
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/   # Shared React components
│   │   ├── context/      # Auth context provider
│   │   ├── pages/        # Page components
│   │   └── services/     # API client
│   ├── public/
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml        # Development
├── docker-compose.prod.yml   # Production
└── README.md
```

## Quick Start (Development)

### Prerequisites

- Docker and Docker Compose
- (Optional) Node.js 20+ and Python 3.11+ for local development without Docker

### 1. Clone and configure

```bash
git clone https://github.com/wjeiv/transformation-coaching.git
cd transformation-coaching

# Create backend environment file
cp backend/.env.example backend/.env
# Edit backend/.env with your values (see Environment Variables below)
```

### 2. Start with Docker Compose

```bash
docker-compose up --build
```

This starts:
- **PostgreSQL** on port 5432
- **Backend API** on http://localhost:8000
- **Frontend** on http://localhost:3000

### 3. Access the application

- **Frontend**: http://localhost:3000
- **API docs**: http://localhost:8000/docs
- **Default admin**: `admin@transformationcoaching.com` / `changeme123!`

> **Important**: Change the default admin password immediately after first login.

## Environment Variables

Create `backend/.env` from `backend/.env.example`:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://tc_user:tc_password@db:5432/transformation_coaching` |
| `SECRET_KEY` | JWT signing key | (generate with `openssl rand -hex 32`) |
| `GARMIN_ENCRYPTION_KEY` | Fernet key for credential encryption | (generate with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`) |
| `FIRST_ADMIN_EMAIL` | Initial admin account email | `admin@transformationcoaching.com` |
| `FIRST_ADMIN_PASSWORD` | Initial admin account password | `changeme123!` |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID (optional) | — |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret (optional) | — |
| `CORS_ORIGINS` | Allowed CORS origins | `http://localhost:3000` |

## Local Development (without Docker)

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

pip install -r requirements.txt

# Start PostgreSQL locally or update DATABASE_URL to point to your instance
# Run migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm start
```

## Testing

### Backend Tests

```bash
cd backend
pip install -r requirements.txt  # includes test dependencies

# Run all tests (excluding Garmin integration)
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run Garmin integration tests (requires real credentials)
GARMIN_TEST_EMAIL=your@email.com GARMIN_TEST_PASSWORD=yourpass pytest tests/test_garmin_integration.py -v -s
```

### Frontend Tests

```bash
cd frontend
npm install
npm test
```

## Production Deployment

### Using Docker Compose (recommended for TrueNAS)

```bash
# Create production env file
cp backend/.env.example backend/.env
# Edit with production values — use strong secrets!

# Build and start
docker-compose -f docker-compose.prod.yml up --build -d

# Run database migrations
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

The production setup includes:
- **Nginx** reverse proxy serving the React build and proxying API requests
- **Health checks** on all services
- **Restart policies** for reliability
- **Non-root** container users

### Security Checklist

- [ ] Change default admin password
- [ ] Generate strong `SECRET_KEY` and `GARMIN_ENCRYPTION_KEY`
- [ ] Set `CORS_ORIGINS` to your actual domain
- [ ] Enable HTTPS (configure in Nginx or use a reverse proxy like Traefik)
- [ ] Set up database backups
- [ ] Review and restrict Docker network access

## API Endpoints

### Public
- `POST /api/v1/public/contact` — Submit contact form
- `GET /health` — Health check

### Authentication
- `POST /api/v1/auth/register` — Register new athlete
- `POST /api/v1/auth/login` — Login
- `POST /api/v1/auth/refresh` — Refresh JWT token
- `GET /api/v1/auth/me` — Get current user profile
- `GET /api/v1/auth/google/url` — Get Google OAuth URL
- `GET /api/v1/auth/google/callback` — Google OAuth callback

### Admin (requires admin role)
- `GET /api/v1/admin/stats` — Dashboard statistics
- `GET /api/v1/admin/users` — List users (with filters)
- `POST /api/v1/admin/users` — Create user
- `PUT /api/v1/admin/users/{id}` — Update user
- `DELETE /api/v1/admin/users/{id}` — Delete user
- `GET /api/v1/admin/contacts` — List contact submissions

### Coach (requires coach role)
- `GET /api/v1/coach/athletes` — List linked athletes
- `POST /api/v1/coach/athletes/{id}/link` — Link athlete
- `DELETE /api/v1/coach/athletes/{id}/unlink` — Unlink athlete
- `GET /api/v1/coach/athletes/{id}/garmin-status` — Check athlete Garmin connection
- `GET /api/v1/coach/workouts` — Get coach's Garmin workouts
- `POST /api/v1/coach/workouts/share` — Share workouts with athlete

### Athlete (requires athlete role)
- `GET /api/v1/athlete/coaches` — List available coaches
- `POST /api/v1/athlete/coach/{id}` — Select coach
- `GET /api/v1/athlete/workouts` — Get shared workouts
- `POST /api/v1/athlete/workouts/import` — Import workouts to Garmin
- `DELETE /api/v1/athlete/workouts/{id}` — Remove shared workout

### Garmin (requires authentication)
- `POST /api/v1/garmin/connect` — Connect Garmin account
- `DELETE /api/v1/garmin/disconnect` — Disconnect Garmin account
- `GET /api/v1/garmin/status` — Get connection status
- `POST /api/v1/garmin/test` — Test Garmin connectivity

## How Garmin Integration Works

1. **Coach connects** their Garmin account via Settings (credentials encrypted with AES-256)
2. **Coach browses** their Garmin workouts in the Coach Dashboard
3. **Coach selects** workouts and an athlete, then clicks Share
4. **Athlete sees** shared workouts in their Athlete Dashboard
5. **Athlete imports** workouts directly to their Garmin Connect account
6. **Sync status** is tracked with human-readable error messages and recommendations

> **Note**: Garmin does not offer a public OAuth API for workout management. This app uses the same authentication method as the official Garmin Connect mobile app via the `python-garminconnect` library.

## Original Prompt (Opus 4.6)
I need to create a website for a personal coaching business.  The website should be attractive to potential customers, easy to navigate for current customers, and useful for coaches and me (the administrator).  The following are user, feature, and non-functional requirements and expectations:

User Requirements:
1. The website should support four personas
    A: The administrator: This is essentially me.  I need to be able to access the website and be able to see a list of current users on the platform and simple stats about them, such as when they've logged in, and other typical user information.  I need a way to create a new account or remove an account, identify that account as a coach or athlete (or admin).
    B: The coach: This is for the business owner.  Should be able to link and unlink to athlete accounts, and share specific garmin workouts to specific athletes
    C: The athlete: This is the paying customer who is linked to a coach.  This athlete can create their own account, authenticate via google if they wish, and choose their coach from the list of coaches available.  They should be able to link their garmin connect account (more on that later) and push or update workouts to their garmin connect account that their coach has shared with them.
    D: The potential customer: The general website (without logging in) needs to have a pleasant presentation showing the overall mission/charter of the business and invite potential customers to reach out for the services that the coach provides.

Feature Requirements:
1. The website needs to allow athletes to create an account.  Only an administrator can create a coach account.
2. The website needs to have a feature where the athlete and coach enter their credentials to garmin connect in order to get access to the garmin connect API
3. If there extra steps for us to access the garmin connect API for a specific user, such as an API KEY, the steps to gather this are clearly described in the website, along with a way to paste that key into our website for storage and use in sharing workouts
4. The coach must be able to view all of their garmin workouts (which can be strength, bike, swim, or running type workouts)
5. The coach must be select workouts from the list and select an athlete to share them with
6. The website must be able to verify connectivity to the athletes garmin connect data when the coach selects the athlete so the coach knows immediately if the sync will succeed or not.  Provide ample human-readable responses for success and failure to help diagnose if something goes wrong.  (like if the athlete hasn't provided an API TOKEN if such a thing is required
7. The athlete must be able to log in and see the workouts that the coach has shared.
8. The athlete can select workouts to import into their garmin connect account.
9. The athlete must be able to remove workouts from the website once they've imported them, if they want to.

Non-Functional Requirements:
1. In the past, I've used the garmin_connect python library to achieve a lot of this.  Do research to decide the best path to achieve the use cases around exporting workouts from one garmin account -> importing those workouts into another account.  I have an existing git repository that does this with limited success: @https://github.com/wjeiv/python-garminconnect.  I specifically wrote @client_pull_workouts.py and @coach_push_workouts.py.
2. It would be ideal for the website to have a good mobile user experience.
3. Use a backend database (SQL is ok) to keep all of this information.
4. Design with security in mind.  Do not let vulnerabilities exist.
5. The solution should be containerized so I can develop in this environment and deploy in a completely different environment, like my TrueNAS server
6. Test suite should include connectivity (actually connectivity) to garmin connect, even if it requires entering credentials.
7. The website's branding is all around Transformation Coaching.  Branding (the dragonfly), mission statement, can all be found on @https://www.facebook.com/profile.php?id=61582142645650
8. The repo for this will be @https://github.com/wjeiv/transformation-coaching.  It is currently empty and you will responsible for building it out for this solution.
9. I expect full test suites, coverage tests, and explicit instructions on build, test, containerization, and deployment so it can be done out of cycle by a human.


## License

Private — All rights reserved.
