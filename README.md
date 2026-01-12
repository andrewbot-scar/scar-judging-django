# scar-judging-django
Scar Judging System Part 2
[README.md](https://github.com/user-attachments/files/24557378/README.md)
# SCAR Judge Portal - Django Version

A tournament judging application for SCAR (SoCal Attack Robots) combat robotics events.

## Tech Stack

- **Backend**: Django 4.2 + Django REST Framework
- **Database**: PostgreSQL
- **Frontend**: React (same as Node.js version)
- **Integrations**: Challonge API, Discord Webhooks, RobotCombatEvents scraping

## Features

- Multi-tournament event management
- 3-judge scoring system (Aggression/Damage/Control)
- Real-time judge status tracking
- Auto-finalization when all judges submit
- Challonge bracket synchronization
- Discord match result notifications
- Robot image scraping from RobotCombatEvents
- Repair timer tracking (20-minute countdown)
- Active "Now Fighting" match indicator
- Spectator mode for public viewing

## Local Development

### Prerequisites

- Python 3.11+
- PostgreSQL (or use SQLite for local dev)

### Setup

```bash
# Clone the repo
git clone https://github.com/yourusername/scar-judging-django.git
cd scar-judging-django

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env
# Edit .env with your settings

# Run migrations
python manage.py migrate

# Create superuser (for admin panel)
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

The API will be available at `http://localhost:8000/api/`

### Admin Panel

Access the Django admin at `http://localhost:8000/admin/` to manage:
- Events
- Judge scores
- Active matches
- Repair timer resets

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SECRET_KEY` | Django secret key | Yes |
| `DEBUG` | Debug mode (True/False) | No (default: False) |
| `DATABASE_URL` | PostgreSQL connection URL | Yes (prod) |
| `ALLOWED_HOSTS` | Comma-separated allowed hosts | Yes (prod) |
| `CORS_ALLOWED_ORIGINS` | Comma-separated CORS origins | Yes |
| `CHALLONGE_API_KEY` | Challonge API key | Yes |
| `CHALLONGE_USERNAME` | Challonge username | No |

## API Endpoints

### Events
- `GET /api/events` - List all events
- `POST /api/events` - Create/update event
- `GET /api/events/:eventId` - Get event details
- `DELETE /api/events/:eventId` - Delete event

### Tournaments (Challonge Proxy)
- `GET /api/tournaments/:id` - Get tournament with matches

### Judge Scoring
- `POST /api/matches/:matchId/scores` - Submit judge scores
- `GET /api/matches/:matchId/scores` - Get score summary
- `GET /api/matches/:matchId/scores/details` - Get detailed breakdown
- `DELETE /api/matches/:matchId/scores/:judgeId` - Delete judge's score

### Active Matches
- `GET /api/events/:eventId/active-matches` - Get active matches
- `POST /api/events/:eventId/active-match` - Set active match
- `DELETE /api/events/:eventId/active-match/:tournamentId` - Clear active match

### Repair Timers
- `GET /api/events/:eventId/repair-resets` - Get repair resets
- `POST /api/events/:eventId/repair-reset` - Reset robot's timer
- `DELETE /api/events/:eventId/repair-reset/:robotName` - Clear reset

### Discord
- `POST /api/events/:eventId/test-discord` - Test webhook

### Utilities
- `GET /api/scrape-rce?url=...` - Scrape robot images
- `GET /api/health` - Health check

## Deployment (Railway)

1. Create a new Railway project
2. Add a PostgreSQL database
3. Connect your GitHub repo
4. Set environment variables:
   - `SECRET_KEY` (generate a new one)
   - `CHALLONGE_API_KEY`
   - `ALLOWED_HOSTS` (your Railway domain)
   - `CORS_ALLOWED_ORIGINS` (your frontend domain)
5. Deploy!

Railway will automatically:
- Detect the Python project
- Install dependencies from `requirements.txt`
- Run migrations via `Procfile`
- Start the Gunicorn server

## Migration from Node.js Version

The API endpoints are identical, so the React frontend works without changes. Just update the `REACT_APP_API_URL` to point to the Django backend.

Database migration:
1. Export events from old PostgreSQL
2. Import into new Django database
3. Run `python manage.py migrate` to ensure schema is correct

## License

MIT
