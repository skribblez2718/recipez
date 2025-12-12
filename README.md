# Recipez

<p align="center">
  <img src="docs/img/recipez.png" alt="Recipez Logo" width="200">
</p>

A full-featured recipe management web application with AI-powered recipe generation and grocery list organization.

## Overview

Recipez is a Flask-based web application for managing, organizing, and sharing recipes. It features user authentication, recipe CRUD operations with image uploads, and AI-powered features for generating recipes from ingredients and creating organized grocery lists from multiple recipes.

## Features

- **Recipe Management** - Create, edit, and delete recipes with images, ingredients, and step-by-step instructions
- **Category Organization** - Organize recipes into categories for easy browsing
- **Ingredient Tracking** - Manage ingredients with quantities and measurements
- **AI Recipe Generation** - Generate new recipes from ingredients or descriptions using OpenAI-compatible LLMs
- **AI Grocery Lists** - Create organized grocery lists from multiple selected recipes
- **User Authentication** - Secure registration and login with email verification
- **Search & Filter** - Find recipes quickly with search and filtering
- **Dark Mode** - Toggle between light and dark themes
- **Responsive Design** - Works on desktop and mobile devices

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Flask 3.1+, SQLAlchemy, Flask-Migrate |
| Database | PostgreSQL 16 |
| Frontend | Tailwind CSS v4, Bootstrap 5.3, Jinja2 |
| AI | LangChain with OpenAI-compatible LLMs |
| Production | Gunicorn, Docker |
| Security | Argon2 password hashing, JWT, CSRF protection |

## Installation

### Prerequisites

- Python 3.11+
- PostgreSQL 16 (or Docker)
- Node.js (for Tailwind CSS compilation, development only)

---

### Option A: Docker Setup (Recommended)

Docker provides the easiest setup with all dependencies bundled.

#### Single Container Mode (App + PostgreSQL)

This runs both the application and PostgreSQL database in Docker containers:

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/recipez.git
cd recipez

# 2. Copy and configure environment file
cp .env.docker.example .env.docker

# 3. Edit .env.docker and set required values:
#    - SECRET_KEY (generate with: python -c "import secrets; print(secrets.token_hex(32))")
#    - DB_PASSWORD (generate with: python -c "import secrets; print(secrets.token_urlsafe(32))")
#    - RECIPEZ_ENCRYPTION_KEY (generate with: python -c "import secrets; print(secrets.token_hex(32))")
#    - RECIPEZ_HMAC_SECRET (generate with: python -c "import base64, secrets; print(base64.b64encode(secrets.token_bytes(64)).decode())")

# 4. Start the application
./docker-start.sh start

# Or with seed data for a fresh installation:
./docker-start.sh start --init

# 5. Access at http://localhost:5000
```

**Docker Management Commands:**

```bash
./docker-start.sh start          # Start all services
./docker-start.sh stop           # Stop all services
./docker-start.sh logs           # View application logs
./docker-start.sh status         # Check container status
./docker-start.sh shell          # Open bash shell in app container
./docker-start.sh db-shell       # Open PostgreSQL shell
./docker-start.sh migrate        # Run database migrations
./docker-start.sh backup         # Backup database
./docker-start.sh clean          # Remove containers and volumes (DESTRUCTIVE)
```

#### External Database Mode (Separate Machines)

To run the application container separately from the database:

```bash
# 1. Set up PostgreSQL on your database server
#    - Create database: recipez
#    - Create schema: recipez
#    - Create user with appropriate permissions

# 2. Configure .env.docker with DATABASE_URL:
DATABASE_URL=postgresql+psycopg://user:password@db-server.example.com:5432/recipez?options=-c%20search_path=recipez

# 3. Start with external database profile
./docker-start.sh start-external

# Or using docker compose directly:
docker compose --profile external-db up -d
```

---

### Option B: Local Python Setup

For development or when you prefer running Python directly:

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/recipez.git
cd recipez

# 2. Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy and configure environment file
cp .env.example .env

# 5. Edit .env and set required values:
#    - SECRET_KEY
#    - DATABASE_URL (e.g., postgresql+psycopg://user:pass@localhost:5432/recipez?options=-c%20search_path=recipez)

# 6. Set up PostgreSQL database
#    - Create database: recipez
#    - Create schema: recipez

# 7. Run database migrations
flask db upgrade

# 8. Initialize the database (optional, adds seed data)
flask init-db

# 9. Start the development server
flask run
```

The application will be available at `http://localhost:5000`.

---

## Configuration

### Required Environment Variables

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Flask session encryption key |
| `DB_PASSWORD` | Database password (Docker mode) |
| `DATABASE_URL` | Full PostgreSQL connection string (Python mode or external DB) |
| `RECIPEZ_ENCRYPTION_KEY` | Data encryption key |
| `RECIPEZ_HMAC_SECRET` | HMAC signing secret |

### Optional Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_ENV` | `production` | Environment mode (`development` or `production`) |
| `DOMAIN` | `recipez.local` | Application domain for cookies |
| `OPENAI_API_KEY` | - | API key for AI features |
| `OPENAI_API_BASE` | `https://api.openai.com/v1` | OpenAI API endpoint |
| `OPENAI_RECIPE_MODEL_ID` | `gpt-3.5-turbo` | Model for recipe generation |
| `OPENAI_GROCERY_MODEL_ID` | `gpt-3.5-turbo` | Model for grocery lists |
| `RECIPEZ_SENDER_PASSWORD` | - | Gmail app password for email verification |
| `APP_PORT` | `5000` | Port to expose (Docker mode) |
| `INIT_DB` | `false` | Initialize with seed data on startup |

### Database Configuration (Docker Mode)

For the bundled PostgreSQL container, use component-based configuration:

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_HOST` | `postgres` | Database hostname |
| `DB_PORT` | `5432` | Database port |
| `DB_USER` | `recipez` | Database username |
| `DB_NAME` | `recipez` | Database name |
| `DB_SCHEMA` | `recipez` | Database schema |
| `DB_PASSWORD` | - | Database password (required) |

For external databases, set `DATABASE_URL` directly and the component variables will be ignored.

---

## Development

```bash
# Run tests
python -m pytest

# Run tests with coverage
python -m pytest --cov=recipez tests/

# Format code
black recipez/ tests/

# Database migrations
flask db migrate -m "Description of changes"
flask db upgrade
```

---

## License

Recipez is dual-licensed:

### AGPL-3.0 (Default)

This project is licensed under the **GNU Affero General Public License v3.0** (AGPL-3.0). This means:

- You can use, modify, and distribute this software freely
- If you modify and deploy this software (including as a network service), you must release your complete source code under AGPL-3.0
- See the [LICENSE](LICENSE) file for full terms

### Commercial License

A commercial license is available for organizations that:
- Cannot comply with AGPL-3.0 requirements
- Want to use this software in proprietary products
- Need additional support or features

For commercial licensing inquiries, please contact the maintainer.
