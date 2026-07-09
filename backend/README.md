# SaaS Stock Deposit Control - Backend

Backend service for the SaaS Stock Deposit Control application. Built with FastAPI, SQLAlchemy 2.0 (Async), and MySQL.

## Prerequisites
- Python 3.10+
- MySQL Server

## Setup & Local Installation

1. **Activate the Virtual Environment:**
   ```bash
   source venv/bin/activate
   ```

2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables:**
   Create a `.env` file in the root of the backend folder:
   ```env
   DB_USER=root
   DB_PASSWORD=your_password
   DB_HOST=localhost
   DB_PORT=3306
   DB_NAME=stock_deposit_control
   DATABASE_URL=mysql+aiomysql://root:your_password@localhost:3306/stock_deposit_control
   ```

4. **Run Database Migrations:**
   ```bash
   alembic upgrade head
   ```

5. **Start the Development Server:**
   Run from the `backend/` directory:
   ```bash
   uvicorn api.main:app --reload
   ```
   The API will be available at `http://localhost:8000`.
   Interactive API documentation (Swagger UI) will be at `http://localhost:8000/docs`.

## Architecture
This project follows a strict **Hexagonal Architecture** layout:
- **`api/`**: Entry layer (controllers, routers, HTTP middlewares)
- **`app/`**: Core domain layer (pure domain models, Pydantic schemas, ports/interfaces, and services)
- **`adapters/`**: Infrastructure layer (outbound database repositories using SQLAlchemy ORM, external API clients)
