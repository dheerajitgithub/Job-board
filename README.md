# Job-board

# Job Recruitment & Hiring Portal

A complete recruitment platform where organizations can **post jobs** and candidates can **apply**.  
The system manages the **end-to-end hiring process**, including job postings, applications, ATS scoring, hiring rounds, tests, reminders, and scheduling.

---

## 🚀 Features

- **Job Posting:** Organizations can create and manage job postings.  
- **Candidate Applications:** Candidates can apply for available jobs.  
- **ATS Screening:** Candidates with ATS scores above the threshold proceed to the hiring flow.  
- **Hiring Procedure:**
  - Psychometric Test  
  - Screening Test  
  - Dynamic Rounds (companies can configure any number of rounds)  
- **Automated Scheduling & Reminders:** Integrated scheduler for interview reminders, test notifications, and follow-ups.  
- **Scalable Architecture:** Designed to handle multiple organizations and large candidate pools.  

---

## 🛠️ Tech Stack

This project uses the following tools and technologies:

- **Backend:** Python, Flask  
- **Database:** SQLAlchemy / PostgreSQL (or MySQL, based on configuration)  
- **Authentication:** JWT-based login & session management  
- **Task Scheduling:** Celery + Redis for background jobs (reminders, emails, etc.)  
- **Frontend (optional if included):** HTML, CSS, JavaScript (extendable with React/Vue)  
- **Others:** Docker (for containerization), Git/GitHub for version control  

---

## ⚙️ Setup & Installation

Follow the steps below to set up the project locally:

# 1) Create a project folder and go inside it
mkdir JobBoard && cd JobBoard

# 2) Create a virtual environment
py -m venv venv          # (use `python` if `py` isn’t available)

# 3) Activate the virtual environment
.\venv\Scripts\Activate.ps1    # PowerShell
# or
venv\Scripts\activate.bat      # CMD

# 4) Upgrade pip and install Django
python -m pip install --upgrade pip
pip install django

# 5) Create a Django project (use "." to avoid double-nesting folders)
django-admin startproject config .

# 6) Create an app (example: "jobs")
python manage.py startapp jobs

# 7) Register the app in settings.py
#   Open config/settings.py and add 'jobs' to INSTALLED_APPS:
#   INSTALLED_APPS = [
#       ...
#       'jobs',
#   ]

# 8) Make initial migrations and migrate DB
python manage.py makemigrations
python manage.py migrate

# 9) (Optional) Create an admin user
python manage.py createsuperuser

# 10) Run the development server
python manage.py runserver (or) python manage.py runserver 0.0.0.0:8000
git clone <your-repo-url>
cd <project-folder>
