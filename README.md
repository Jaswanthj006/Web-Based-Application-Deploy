# Chemical Equipment Parameter Visualizer (Hybrid Web + Desktop)

A hybrid application that runs as both a **Web Application** (React + Chart.js) and a **Desktop Application** (PyQt5 + Matplotlib), sharing a common **Django REST** backend for chemical equipment data visualization and analytics.

## Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Frontend (Web) | React.js + Chart.js | Table + charts in browser |
| Frontend (Desktop) | PyQt5 + Matplotlib | Same visualization on desktop |
| Backend | Python Django + Django REST Framework | Common API |
| Data | Pandas | CSV parsing & analytics |
| Database | SQLite | Store last 5 uploaded datasets |
| Version Control | Git & GitHub | Collaboration & submission |

## Features

1. **CSV Upload** – Web and Desktop clients upload CSV files to the backend.
2. **Data Summary API** – Total count, averages (Flowrate, Pressure, Temperature), equipment type distribution.
3. **Visualization** – Charts via Chart.js (Web) and Matplotlib (Desktop).
4. **History** – Last 5 uploaded datasets with summary.
5. **PDF Report** – Generate PDF report (requires login).
6. **Basic Authentication** – Register / Login with token auth; upload and PDF require auth.

## Project Structure

```
Web-Based-Application/
├── backend/                 # Django REST API
│   ├── backend/             # settings, urls
│   ├── equipment/           # app: models, views, serializers, services
│   ├── manage.py
│   └── requirements.txt
├── frontend-web/            # React + Chart.js
│   ├── src/
│   └── package.json
├── frontend-desktop/        # PyQt5 + Matplotlib
│   ├── main.py
│   └── requirements.txt
├── sample_equipment_data.csv   # Sample CSV for demo
└── README.md
```

## Setup Instructions

### 1. Backend (Django)

```bash
cd backend
python -m venv venv
# On Windows: venv\Scripts\activate
source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Backend runs at **http://127.0.0.1:8000**. API base path: `/api/`.

### 2. Web Frontend (React)

```bash
cd frontend-web
npm install
npm run dev
```

Web app runs at **http://localhost:3000**. It proxies `/api` to the Django backend.

### 3. Desktop Frontend (PyQt5)

Ensure the backend is running, then:

```bash
cd frontend-desktop
python -m venv venv
source venv/bin/activate   # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python main.py
```

Set `API_BASE` if backend is not at `http://127.0.0.1:8000/api`:

```bash
export API_BASE=http://127.0.0.1:8000/api
python main.py
```

### 4. Sample Data

Use `sample_equipment_data.csv` in the project root for testing. Columns: **Equipment Name**, **Type**, **Flowrate**, **Pressure**, **Temperature**.

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/auth/register/` | No | Register; returns token |
| POST | `/api/auth/login/` | No | Login; returns token |
| POST | `/api/upload/` | Token | Upload CSV |
| GET | `/api/history/` | No | List last 5 datasets |
| GET | `/api/summary/<id>/` | No | Summary for dataset |
| GET | `/api/data/<id>/` | No | Full table data |
| GET | `/api/report/<id>/pdf/?token=<token>` | Token | Download PDF report |

## Submission

- Source code on **GitHub** (backend + both frontends).
- **README** with setup instructions (this file).
- Short **demo video** (2–3 minutes).
- Optional: deployment link for web version.

Submit via: https://forms.gle/bSiKezbM4Ji9xnw66
