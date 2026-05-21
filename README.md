# This is backend code for our Volvo project
# Volvo IDEA (Initiative Definition & Evaluation Application) - Prototype

This repository contains the prototype for the Volvo IDEA project. It includes a fully functional FastAPI backend and a responsive, Vanilla JavaScript frontend designed according to Volvo's corporate identity guidelines.

## Tech Stack

**Frontend:**
* HTML5
* CSS3 (Custom properties, Flexbox)
* Vanilla JavaScript (ES6+, Fetch API)
* Bootstrap 5 (UI components, Grid system)

**Backend:**
* Python 3.14
* FastAPI
* Pydantic
* SQLAlchemy (ORM)
* PostgreSQL (via Docker)
* Uvicorn (ASGI server)

## Features

* **Submit New Initiatives:** A step-by-step tile-based form with real-time HTML5 validation.
* **Track Status:** Users can track the progress of their initiative using an auto-generated Tracking ID (UUID).
* **Verifier Dashboard:** A protected route for verifiers to log in, view all submitted leads in a table, preview full details in a modal, and update the initiative's status.
* **Persistent Storage:** Fully relational PostgreSQL database schema for reliable data retention and future PowerBI integration.

## How to run locally

To run this project, you need to start: the Backend server, the Frontend interface and a PostgreSQL database.
### 1. Start the Database
The backend requires a PostgreSQL database. The easiest way to run this is via Docker. Open your terminal and execute:
```bash
docker run --name idea-postgres -e POSTGRES_USER=admin -e POSTGRES_PASSWORD=cisco123 -e POSTGRES_DB=idea_db -p 5433:5432 -d postgres
```
### 2. Start the Backend
Open your terminal, navigate to the project directory, and run the following commands:

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
  # On Windows:
    venv\Scripts\activate
  # On macOS/Linux:
    source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the FastAPI server
uvicorn main:app --reload
```
The API will be available at http://127.0.0.1:8000. SQLAlchemy will automatically detect the database connection and generate the required tables on startup.

### 3. Start the Frontend
Since the frontend uses pure HTML/JS/CSS, you can open the index.html file in your browser.
However, it is recommended to use a local server:

* If using VS Code, install the **Live Server** extension, right-click on index.html, and select "Open with Live Server".

Alternatively, you can run a Python HTTP server in the project directory:
```
python -m http.server 5500
```
and open http://localhost:5500 in your browser.
