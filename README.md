# EasyTest Backend - Django REST API

Django REST API backend for the EasyTest Online Exam & Analytics Platform.

## 🚀 Features

- **JWT Authentication**: Secure token-based authentication
- **Exam Management**: Create, update, delete, and freeze exams
- **Question Bank**: Manage questions with AI generation support
- **Participant Management**: Import participants via CSV/Excel
- **Reports & Analytics**: Detailed exam and participant analytics
- **Dashboard**: Overview statistics and performance metrics
- **Leaderboard**: Rankings and top performers
- **MySQL Database**: Production-ready database support

## 📋 Prerequisites

- Python 3.8+
- MySQL 5.7+ or MySQL 8.0+
- pip and virtualenv

## 🛠️ Installation

### 1. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Database

Create a MySQL database:

```sql
CREATE DATABASE easytest CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```env
# Database Configuration
DB_NAME=easytest
DB_USER=root
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=3306

# Django Secret Key
SECRET_KEY=your-secret-key-here-change-in-production

# Debug Mode
DEBUG=True

# Allowed Hosts (comma-separated)
ALLOWED_HOSTS=localhost,127.0.0.1

# CORS Allowed Origins (comma-separated)
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
```

### 5. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create Superuser

```bash
python manage.py createsuperuser
```

### 7. Run Development Server

```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000/api/`

## 📡 API Endpoints

### Authentication
- `POST /api/auth/login/` - User login

### Exams
- `GET /api/exams/` - List all exams
- `POST /api/exams/` - Create exam
- `GET /api/exams/{id}/` - Get exam details
- `PATCH /api/exams/{id}/` - Update exam
- `DELETE /api/exams/{id}/` - Delete exam
- `POST /api/exams/{id}/freeze/` - Freeze exam
- `GET /api/exams/{id}/snapshot/` - Download exam snapshot
- `POST /api/exams/{id}/assign_questions/` - Assign questions to exam

### Questions
- `GET /api/questions/` - List all questions
- `POST /api/questions/` - Create question
- `GET /api/questions/{id}/` - Get question details
- `PATCH /api/questions/{id}/` - Update question
- `DELETE /api/questions/{id}/` - Delete question
- `POST /api/questions/generate/` - AI generate questions

### Participants
- `GET /api/participants/` - List participants (optional: `?exam_id={id}`)
- `POST /api/participants/` - Create participant
- `GET /api/participants/{id}/` - Get participant details
- `PATCH /api/participants/{id}/` - Update participant
- `DELETE /api/participants/{id}/` - Delete participant
- `POST /api/participants/import_participants/` - Import from CSV/Excel
- `POST /api/participants/{id}/assign_clicker/` - Assign clicker ID

### Reports
- `GET /api/reports/exams/{id}/` - Get exam report
- `GET /api/reports/exams/{id}/export/?format=excel|csv` - Export report

### Dashboard
- `GET /api/dashboard/` - Get dashboard data

### Leaderboard
- `GET /api/leaderboard/exams/{id}/` - Get exam leaderboard

## 🔐 Authentication

All endpoints (except login) require JWT authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your-token>
```

## 📊 Database Models

### Exam
- Title, description, duration
- Positive/negative marking
- Revisable mode
- Frozen status

### Question
- Text, type (MCQ, True/False, Multiple Select)
- Options, correct answer
- Difficulty level
- Tags

### Participant
- Name, email
- Clicker ID

### ExamAttempt
- Score, percentage
- Correct/wrong/unattempted counts
- Time taken

### Answer
- Selected answer
- Correctness
- Time taken per question

## 🔧 Development

### Running Tests

```bash
python manage.py test
```

### Creating Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### Accessing Admin Panel

Visit `http://localhost:8000/admin/` and login with superuser credentials.

## 📝 Notes

- **AI Question Generation**: The `/api/questions/generate/` endpoint currently uses mock data. Integrate with OpenAI, Anthropic, or similar API for production.
- **File Uploads**: CSV/Excel import supports columns: `name`, `email`, `clicker_id` (optional)
- **CORS**: Configured for frontend at `http://localhost:5173` by default
- **JWT Tokens**: Access tokens expire in 1 day, refresh tokens in 7 days

## 🚀 Production Deployment

1. Set `DEBUG=False` in `.env`
2. Generate a new `SECRET_KEY`
3. Configure proper `ALLOWED_HOSTS`
4. Set up static file serving
5. Use a production WSGI server (gunicorn, uWSGI)
6. Configure reverse proxy (nginx)
7. Set up SSL certificates

## 📄 License

Proprietary - All rights reserved

