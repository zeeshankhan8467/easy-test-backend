# EasyTest Backend - Quick Setup Guide

## 🚀 Quick Start

### 1. Database Setup

First, create the MySQL database:

```bash
mysql -u root -p
```

```sql
CREATE DATABASE easytest CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EXIT;
```

### 2. Environment Configuration

Copy `.env.example` to `.env` and update with your database credentials:

```bash
cp .env.example .env
# Edit .env with your MySQL credentials
```

### 3. Install and Setup

```bash
# Activate virtual environment
source ../easytest-backend-venv/bin/activate  # or: venv\Scripts\activate on Windows

# Install dependencies (if not already installed)
pip install -r requirements.txt

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
# Enter email, username, and password when prompted
```

### 4. Start Server

```bash
python manage.py runserver
```

API will be available at: `http://localhost:8000/api/`

## 🔑 Creating Test Users

### Via Django Shell

```bash
python manage.py shell
```

```python
from django.contrib.auth.models import User

# Create admin user
admin = User.objects.create_user(
    username='admin',
    email='admin@easytest.com',
    password='admin123',
    is_superuser=True,
    is_staff=True
)

# Create instructor user
instructor = User.objects.create_user(
    username='instructor',
    email='instructor@easytest.com',
    password='instructor123'
)
```

### Via Admin Panel

1. Visit `http://localhost:8000/admin/`
2. Login with superuser credentials
3. Go to "Users" section
4. Add new users

## 📊 Testing API Endpoints

### Login

```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@easytest.com", "password": "admin123"}'
```

### Create Exam (with token)

```bash
curl -X POST http://localhost:8000/api/exams/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Sample Exam",
    "duration": 60,
    "positive_marking": 1.0,
    "negative_marking": 0.25,
    "revisable": true
  }'
```

## 🔧 Troubleshooting

### MySQL Connection Issues

1. Verify MySQL is running: `mysql -u root -p`
2. Check database exists: `SHOW DATABASES;`
3. Verify credentials in `.env` file
4. Ensure MySQL client is installed: `pip install mysqlclient`

### Migration Issues

```bash
# Reset migrations (WARNING: Deletes all data)
python manage.py migrate api zero
python manage.py makemigrations
python manage.py migrate
```

### CORS Issues

If frontend can't connect:
1. Check `CORS_ALLOWED_ORIGINS` in `.env`
2. Ensure frontend URL matches exactly
3. Restart Django server after changing `.env`

### Port Already in Use

```bash
# Use different port
python manage.py runserver 8001
```

## 📝 Next Steps

1. **Connect Frontend**: Update frontend `.env` with `VITE_API_BASE_URL=http://localhost:8000/api`
2. **Create Sample Data**: Use admin panel or API to create exams, questions, participants
3. **Test Integration**: Verify frontend can authenticate and fetch data
4. **AI Integration**: Replace mock AI generation with actual API integration

## 🔐 Security Notes

- Never commit `.env` file to version control
- Use strong `SECRET_KEY` in production
- Set `DEBUG=False` in production
- Configure proper `ALLOWED_HOSTS` for production
- Use HTTPS in production
- Regularly update dependencies

