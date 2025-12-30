# 🏨 Django Hotel Booking Engine API

![Python](https://img.shields.io/badge/Python-3.10%2B-blue) ![Django](https://img.shields.io/badge/Framework-Django-green) ![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL-336791) ![Redis](https://img.shields.io/badge/Queue-Redis-red) ![Celery](https://img.shields.io/badge/Worker-Celery-brightgreen) ![Stripe](https://img.shields.io/badge/Payments-Stripe-blueviolet) ![JWT](https://img.shields.io/badge/Auth-JWT-black)

A robust, production-ready REST API for a hotel booking system. Features dynamic pricing, real-time inventory management, automated expiration of unpaid bookings ("Zombie Killer"), and secure payments via Stripe. Built with **Django REST Framework**, **Celery**, **Redis**, and **Stripe**.

---

## 📋 Table of Contents

- [Features](#-features)
- [API Flow Diagrams](#-api-flow-diagrams)
- [Getting Started](#-getting-started)
- [Running the Application](#️-running-the-application)
- [Configuration Reference](#-configuration-reference)
- [Testing Guide](#-testing-guide)
- [API Documentation](#-api-documentation)
- [Project Structure](#-project-structure)
- [Contributing](#-contributing)
- [License](#-license)

---

## ✨ Features

### 📅 Booking & Inventory

- **Real-time Availability:** Prevents double-booking using atomic database transactions.
- **Dynamic Pricing Engine:** Calculates prices based on:
  - Date ranges (e.g., High Season).
  - Days of the week (e.g., Weekend rates).
  - Room types.
- **The "Zombie Killer" Task:** A background job (Celery) that automatically expires "Pending" bookings if they remain unpaid for more than 15 minutes, releasing inventory back to the pool.

### 💳 Payments (Stripe)

- **Payment Intents:** Secure handling of payments using Stripe's modern API.
- **Webhooks:** Listens for Stripe events to automatically confirm bookings upon successful payment.
- **"God Mode" Testing:** A developer-only feature to instantly confirm payments via API without a frontend (for testing purposes).
- **Refund Handling:** Logic for calculating refunds and penalties based on cancellation policies (48-hour rule).

### 🛠 Technical

- **Authentication:** JWT (JSON Web Token) authentication.
- **Documentation:** Auto-generated Swagger/OpenAPI docs via `drf-spectacular`.
- **Dockerized:** Ready for containerized deployment.

---

## 🌊 API Flow Diagrams

### Complete Booking Workflow

```mermaid
graph TD
    A[Client/Frontend] -->|1. Search Rooms| B[GET /api/search]
    B -->|Returns available rooms| A
    A -->|2. Create Booking| C[POST /api/book]
    C -->|Creates PENDING booking| D[(Database)]
    D -->|Status: PENDING| A

    A -->|3. Initiate Payment| E[POST /api/bookings/ID/checkout]
    E -->|Creates Stripe Intent| F[Stripe API]
    F -->|Returns client_secret| E
    E -->|Returns credentials| A

    A -->|4. Confirm Payment| F
    F -->|5. Payment Succeeded| G[Stripe Webhook]
    G -->|6. POST /api/webhook| H[Django Webhook Handler]
    H -->|Updates booking| D
    D -->|Status: CONFIRMED| H

    H -->|7. Response 200| G
    D -->|Booking confirmed| A
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- PostgreSQL
- Redis (for Celery)
- Stripe CLI (for local webhook testing)

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/booking-engine.git
cd booking-engine

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Variables

Create a `.env` file in the root directory:

```ini
# Django Settings
DEBUG=True
SECRET_KEY=your_django_secret_key_here
DATABASE_URL=postgres://user:password@localhost:5432/booking_db

# Stripe Keys
STRIPE_PUBLIC_KEY=pk_test_your_public_key_here
STRIPE_SECRET_KEY=sk_test_your_secret_key_here
STRIPE_WEBHOOK_KEY=whsec_your_webhook_secret_here

# Celery / Redis Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
```

### 3. Install & Configure PostgreSQL

**On Windows (using PostgreSQL installer):**

1. Download from https://www.postgresql.org/download/windows/
2. Run installer and follow setup wizard
3. Remember the password you set for the `postgres` user
4. Create a new database:
   ```bash
   psql -U postgres
   CREATE DATABASE booking_db;
   \q
   ```

**On macOS (using Homebrew):**

```bash
brew install postgresql@15
brew services start postgresql@15
createdb booking_db
```

**On Linux (Ubuntu/Debian):**

```bash
sudo apt-get update && sudo apt-get install postgresql postgresql-contrib
sudo -u postgres createdb booking_db
```

### 4. Install & Configure Redis

Redis is required for Celery to work properly.

**On Windows:**

1. Download from https://github.com/microsoftarchive/redis/releases
2. Extract and run `redis-server.exe`
3. Or use Windows Subsystem for Linux (WSL):
   ```bash
   wsl
   sudo apt-get install redis-server
   sudo service redis-server start
   ```

**On macOS:**

```bash
brew install redis
brew services start redis
```

**On Linux:**

```bash
sudo apt-get install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

**Verify Redis is running:**

```bash
redis-cli ping  # Should respond with PONG
```

### 5. Install & Configure Stripe CLI

**Download Stripe CLI:**

- Windows: https://github.com/stripe/stripe-cli/releases (download `.exe`)
- macOS: `brew install stripe/stripe-cli/stripe`
- Linux: Download from https://github.com/stripe/stripe-cli/releases

**Authenticate with Stripe:**

```bash
stripe login
# Follow prompts to authenticate with your Stripe account
```

Verify installation:

```bash
stripe --version
```

### 6. Database Migrations

Before running the application for the first time:

```bash
# Apply all database migrations
python manage.py migrate

# Create admin user
python manage.py createsuperuser
# Follow prompts to create your admin account

# (Optional) Load sample data
python manage.py loaddata initial_data  # If fixtures exist
```

---

## 🏃‍♂️ Running the Application

The application requires multiple services running simultaneously. You can run them in separate terminal windows or use Docker Compose.

### Prerequisites Check

Before starting, verify all services are installed and running:

```bash
# Check Python
python --version  # Should be 3.10+

# Check PostgreSQL
psql -U postgres -c "SELECT version();"

# Check Redis
redis-cli ping  # Should respond with PONG

# Check Stripe CLI
stripe --version

# Verify Django installation
python manage.py --version
```

### Running Services in Separate Terminals (Development)

You need **4 terminal windows** to run the full stack:

#### Terminal 1: Django Development Server

```bash
# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Start Django server (default: http://localhost:8000)
python manage.py runserver

# You should see:
# Starting development server at http://127.0.0.1:8000/
```

Access the API at: http://localhost:8000/api/

#### Terminal 2: Celery Worker (Executes Async Tasks)

The worker processes background tasks like sending emails, payment processing, etc.

```bash
# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Start Celery worker
celery -A core worker --loglevel=info --pool=solo

# On Windows, use --pool=solo flag to avoid multiprocessing issues

# You should see:
# celery@yourcomputer ready to accept tasks.
```

**What the worker does:**

- Processes booking expiration (Zombie Killer task)
- Handles email notifications
- Manages async Stripe operations

#### Terminal 3: Celery Beat (Task Scheduler)

The Beat scheduler runs periodic tasks at set intervals.

```bash
# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Start Celery Beat scheduler
celery -A core beat --loglevel=info

# You should see periodic task execution logs
```

**Scheduled tasks:**

- Zombie Killer: Runs every minute to expire unpaid bookings after 15 minutes

#### Terminal 4: Stripe Webhook Listener (Local Testing Only)

For local development, use Stripe CLI to forward webhook events to your server:

```bash
# Authenticate with Stripe (one-time setup)
stripe login

# Start listening for webhook events and forward to local Django server
stripe listen --forward-to localhost:8000/api/webhook/

# You should see:
# Ready! Your webhook signing secret is: whsec_xxxxxxxxxxxxxxxxxxxx
```

**Important:** Copy the signing secret and add it to your `.env`:

```ini
STRIPE_WEBHOOK_KEY=whsec_xxxxxxxxxxxxxxxxxxxx
```

---

---

## 🔧 Configuration Reference

### Celery Configuration

Located in `core/celery.py`:

```python
# Task routing
CELERY_TASK_ROUTES = {
    'bookings.tasks.expire_pending_bookings': {'queue': 'default'},
}

# Task time limits (prevent hanging tasks)
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes hard limit
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes soft limit

# Celery Beat schedule (in core/settings.py)
CELERY_BEAT_SCHEDULE = {
    'expire-pending-bookings': {
        'task': 'bookings.tasks.expire_pending_bookings',
        'schedule': crontab(minute='*/1'),  # Every minute
    },
}
```

### Redis Configuration

Default configuration uses:

- **Broker:** `redis://localhost:6379/0` (tasks)
- **Result Backend:** `redis://localhost:6379/1` (results)
- **Database 2+:** Available for caching/sessions

To use different Redis databases, modify in `.env`:

```ini
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
```

### Stripe Configuration

**Keys location:** `core/settings.py`

```python
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY")
STRIPE_WEBHOOK_KEY = os.getenv("STRIPE_WEBHOOK_KEY")
```

**Webhook endpoint:** `POST /api/webhook/`

---

## 🧪 Testing Guide

### 1. The "Zombie Killer" Flow (Expired Bookings)

To test that bookings expire after 15 minutes:

1. **Create a Booking:** POST to `/api/bookings/`. Status will be `PENDING`.
2. **Wait:** Wait 16 minutes OR manually modify the `created_at` timestamp in DB.
3. **Check Status:** The Celery Beat task runs every minute. It should update status to `EXPIRED`.
4. **Verify Inventory:** You should be able to book the same room again immediately.

### 2. Stripe Payments (Backend Only / "God Mode")

We implemented a special testing flag to bypass the frontend card entry.

**Endpoint:** `POST /api/bookings/{id}/checkout/`

**Request Body:**

```json
{
  "auto_confirm": true
}
```

**Result:** The server contacts Stripe, forces a test charge using a Visa mock, and instantly updates the booking to `CONFIRMED`.

### 3. Stripe Webhooks (Real Simulation)

To test the real integration where Stripe notifies Django:

1. **Start Stripe Listener:**

   ```bash
   stripe listen --forward-to localhost:8000/api/webhook/
   ```

2. **Create a Booking** normally (get the `client_secret`).

3. **Confirm via CLI** (Simulates user paying on frontend):

   ```bash
   stripe payment_intents confirm pi_3Sk... --payment-method=pm_card_visa
   ```

4. **Verify:** Check your terminal. The webhook should hit `/api/webhook/` and you should see "✅ Booking confirmed via Webhook."

### 4. Running Unit Tests

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test bookings

# Run with coverage
coverage run --source='.' manage.py test
coverage report
```

---

## 📚 API Documentation

Once the server is running, visit:

- **Swagger UI:** http://localhost:8000/api/schema/swagger-ui/
- **ReDoc:** http://localhost:8000/api/schema/redoc/
- **Admin Panel:** http://localhost:8000/admin/

### Key Endpoints

| Method | Endpoint                       | Description            |
| ------ | ------------------------------ | ---------------------- |
| GET    | `/api/rooms/search/`           | Search available rooms |
| POST   | `/api/bookings/`               | Create a new booking   |
| GET    | `/api/bookings/{id}/`          | Get booking details    |
| POST   | `/api/bookings/{id}/checkout/` | Initiate payment       |
| POST   | `/api/bookings/{id}/cancel/`   | Cancel a booking       |
| POST   | `/api/webhook/`                | Stripe webhook handler |
| POST   | `/api/auth/login/`             | JWT authentication     |

---

## 📁 Project Structure (actual)

Below is the real file/folder layout discovered in this repository root.

```
Booking Engine/                         # repository root
├── .env.example                        # example env variables
├── .gitignore                          # git ignore rules
├── db.sqlite3                          # local SQLite DB (dev artifact)
├── manage.py                           # Django management entrypoint
├── README.md                           # this file
├── requirements.txt                    # Python dependencies

├── authentication/                     # auth: registration & JWT
│   ├── __init__.py                     # package marker
│   ├── admin.py                        # Django admin registrations
│   ├── apps.py                         # app config
│   ├── models.py                       # auth-related models (users/profiles)
│   ├── serializers.py                  # DRF serializers for auth
│   ├── tests.py                        # unit tests for auth
│   ├── urls.py                         # endpoints: register/login/refresh
│   └── views.py                        # registration & auth views

├── bookings/                           # booking domain logic
│   ├── __init__.py                     # package marker
│   ├── admin.py                        # admin for bookings/models
│   ├── apps.py                         # app config
│   ├── models.py                       # Booking, Reservation, etc.
│   ├── serializers.py                  # DRF serializers for bookings
│   ├── services.py                     # business logic & helpers
│   ├── tasks.py                        # Celery tasks (e.g., expire bookings)
│   ├── tests.py                        # unit tests for bookings
│   ├── urls.py                         # booking-related endpoints
│   └── views.py                        # booking API views

├── core/                               # project core settings & entrypoints
│   ├── __init__.py                     # package marker
│   ├── asgi.py                         # ASGI entrypoint
│   ├── celery.py                       # Celery app configuration
│   ├── settings.py                     # Django settings
│   ├── urls.py                         # root URL config (includes app urls)
│   └── wsgi.py                         # WSGI entrypoint

├── inventory/                          # rooms, room types, availability
│   ├── __init__.py                     # package marker
│   ├── admin.py                        # admin registrations for inventory
│   ├── apps.py                         # app config
│   ├── filters.py                      # DRF filters for search/listing
│   ├── models.py                       # Room, RoomType, PricingRule models
│   ├── serializers.py                  # DRF serializers for inventory
│   ├── services.py                     # inventory helpers & pricing engine
│   ├── tests.py                        # unit tests for inventory
│   ├── urls.py                         # endpoints: room search
│   └── views.py                        # inventory API views

└── user/                               # user profile & wishlist
    ├── __init__.py                     # package marker
    ├── admin.py                        # user admin registrations
    ├── apps.py                         # app config
    ├── models.py                       # Profile, Wishlist models
    ├── serializers.py                  # DRF serializers for user
    ├── tests.py                        # unit tests for user app
    ├── urls.py                         # endpoints: profile, wishlist
    └── views.py                        # user API views

```
