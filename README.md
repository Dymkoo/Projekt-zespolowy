# Volvo IDEA (Initiative Definition & Evaluation Application) - Prototype

This repository contains the prototype for the Volvo IDEA project. It includes a fully functional, secure FastAPI backend and a responsive, Vanilla JavaScript frontend designed strictly according to Volvo's corporate identity (Brand Book) guidelines.
## Tech Stack

**Frontend:**
* HTML5
* CSS3 (Custom properties, Flexbox, Volvo typography)
* Vanilla JavaScript (ES6+, Fetch API)
* Bootstrap 5 (UI components, Grid system)

**Backend:**
* Python 3.14
* FastAPI
* Pydantic
* SQLAlchemy (ORM)
* FastAPI-Mail (Automated email notifications)
* bcrypt (Secure password hashing)
* Uvicorn (ASGI server)

**Deployment & Infrastructure:**
* PostgreSQL 15 (Relational database)
* Docker & Docker Compose (Fully containerized environment)

## Key Features

* **Submit New Initiatives:** A step-by-step tile-based form with real-time HTML5 validation.
* **Track Status:** Users can track the progress of their initiative using an auto-generated Tracking ID (UUID).
* **Role-Based Access Control (RBAC):**
  * **Verifier (Admin):** A protected dashboard to view all submitted leads, preview full details, update statuses, assign leaders, and manage user accounts.
  * **Project Leader:** Restricted access allowing leaders to view and manage only the specific leads assigned to them.
* **Automated Email Notifications:** The system automatically sends emails upon lead submission, status updates, and when a new Project Leader is assigned (generating and sending temporary login credentials).
* **Secure Authentication:** Passwords are encrypted in the database. The system supports secure login sessions and password updates.
* **Persistent Storage:** Fully relational PostgreSQL database schema for reliable data retention and future PowerBI integration.
<br>

## How to run locally

The entire application stack (Frontend, Backend, and Database) is fully containerized.

### 1. Prerequisites
Ensure you have [Docker](https://www.docker.com/) and Docker Compose installed and running on your machine.
<br>
<br>

### 2. Environment Variables
Create a `.env` file in the root directory of the project and provide the following configuration:

```env
DB_PASSWORD=your_secure_db_password
EMAIL_APP_PASSWORD=your_email_app_password
VERIFIER_EMAIL=admin@example.com
VERIFIER_USERNAME=admin_user
VERIFIER_PASSWORD=your_secure_admin_password
```
<br>

### 3. Start the Application
Open your terminal, navigate to the project directory, and run:
```
docker compose up -d --build
```
SQLAlchemy will automatically detect the database connection and generate all required tables on startup.
<br>
<br>

### 4. Access the Project
Once the containers are successfully built and started, you can access the application at:

Frontend (User Interface): http://localhost:5500

Backend (API & Swagger Docs): http://localhost:8000/docs
<br>
<br>

### 5. Stopping the Application
To safely stop the servers and remove the containers, open your terminal and run:
```
docker compose down
```
If you need to completely reset the database (e.g., after altering database schemas or testing new data), run:
```
docker compose down -v
```
