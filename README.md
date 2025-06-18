# Snippets Backend API

**🌐 [Live API Documentation](https://snippets-backend-69z8.onrender.com/swagger/)**

A robust Django REST API for managing and sharing code snippets with syntax highlighting, user authentication, and comprehensive API documentation.

## 🚀 Features

- **Code Snippet Management**: Create, read, update, and delete code snippets
- **Syntax Highlighting**: Automatic syntax highlighting using Pygments with support for 300+ programming languages
- **User Authentication**: JWT-based authentication with custom user model
- **Password Reset**: Email-based password reset functionality
- **API Documentation**: Interactive API documentation with Swagger/OpenAPI
- **Pagination**: Built-in pagination for large datasets
- **Filtering**: Advanced filtering capabilities for snippets
- **CORS Support**: Cross-origin resource sharing enabled for frontend integration
- **Production Ready**: Configured for deployment with Gunicorn and PostgreSQL

## 🛠️ Tech Stack

- **Framework**: Django 4.2.21
- **API**: Django REST Framework 3.16.0
- **Authentication**: JWT (djangorestframework-simplejwt)
- **Database**: SQLite (development) / PostgreSQL (production)
- **Documentation**: drf-spectacular (Swagger/OpenAPI)
- **Syntax Highlighting**: Pygments
- **Deployment**: Gunicorn, Whitenoise
- **CORS**: django-cors-headers

## 📋 Prerequisites

- Python 3.8+
- pip
- PostgreSQL (for production)

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd snippets-backend
```

### 2. Create Virtual Environment

```bash
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Setup

Create a `.env` file in the root directory:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### 5. Database Setup

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create Superuser (Optional)

```bash
python manage.py createsuperuser
```

### 7. Run Development Server

```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000/`

## 📚 API Documentation

### Interactive Documentation

- **Swagger UI**: `http://localhost:8000/swagger/`
- **ReDoc**: `http://localhost:8000/redoc/`
- **OpenAPI Schema**: `http://localhost:8000/api/schema/`

### Authentication Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/register/` | POST | Register a new user |
| `/auth/login/` | POST | Login and get JWT tokens |
| `/auth/login/refresh/` | POST | Refresh JWT token |
| `/auth/logout/` | POST | Logout (blacklist token) |
| `/auth/user/` | GET | Get current user details |
| `/auth/password-reset/` | POST | Request password reset |
| `/auth/password-reset/confirm/` | POST | Confirm password reset |

### Snippet Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/snippets/` | GET, POST | List all snippets / Create new snippet |
| `/snippets/{id}/` | GET, PUT, PATCH, DELETE | Retrieve, update, or delete snippet |
| `/users/` | GET | List all users |
| `/users/{id}/` | GET | Get user details |

### Example API Usage

#### Register a User
```bash
curl -X POST http://localhost:8000/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "securepassword123"
  }'
```

#### Login
```bash
curl -X POST http://localhost:8000/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "securepassword123"
  }'
```

#### Create a Snippet
```bash
curl -X POST http://localhost:8000/snippets/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Hello World in Python",
    "code": "print(\"Hello, World!\")",
    "language": "python",
    "style": "friendly",
    "linenos": true
  }'
```

## 🏗️ Project Structure

```
snippets-backend/
├── authentication/          # User authentication app
│   ├── models.py           # Custom user model
│   ├── views.py            # Authentication views
│   ├── serializers.py      # User serializers
│   ├── urls.py             # Auth URL patterns
│   └── templates/          # Email templates
├── snippets/               # Main snippets app
│   ├── models.py           # Snippet model
│   ├── views.py            # Snippet views
│   ├── serializers.py      # Snippet serializers
│   ├── permissions.py      # Custom permissions
│   └── urls.py             # Snippet URL patterns
├── config/                 # Django settings
│   ├── settings.py         # Main settings
│   ├── urls.py             # Root URL patterns
│   └── deployment_settings.py
├── requirements.txt        # Python dependencies
├── build.sh               # Deployment script
└── manage.py              # Django management
```

## 🔧 Configuration

### Database Configuration

For production, update the database settings in `config/settings.py`:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'your_db_name',
        'USER': 'your_db_user',
        'PASSWORD': 'your_db_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### Email Configuration

Configure email settings for password reset functionality:

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
```

## 🚀 Deployment

### Using the Build Script

The project includes a `build.sh` script for easy deployment:

```bash
chmod +x build.sh
./build.sh
```

### Manual Deployment

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Collect Static Files**:
   ```bash
   python manage.py collectstatic --no-input
   ```

3. **Run Migrations**:
   ```bash
   python manage.py migrate
   ```

4. **Create Superuser** (optional):
   ```bash
   python manage.py createsuperuser
   ```

### Environment Variables

Set these environment variables for production:

```bash
export SECRET_KEY="your-production-secret-key"
export DEBUG=False
export DATABASE_URL="postgresql://user:password@localhost/dbname"
export ALLOWED_HOSTS="your-domain.com,www.your-domain.com"
```

## 🧪 Testing

Run the test suite:

```bash
python manage.py test
```

## 📝 API Models

### Snippet Model

```python
{
    "id": 1,
    "created": "2024-01-01T12:00:00Z",
    "title": "Hello World",
    "code": "print('Hello, World!')",
    "linenos": false,
    "language": "python",
    "style": "friendly",
    "owner": 1,
    "highlighted": "<pre><code>...</code></pre>"
}
```

### User Model

```python
{
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "first_name": "Test",
    "last_name": "User"
}
```

## 🔒 Security Features

- JWT token authentication
- Password validation
- CORS protection
- CSRF protection
- SQL injection protection
- XSS protection

## 📄 License

**Copyright Notice**: This project and its codebase are the intellectual property of Alec Hsu. This project should not be copied, reproduced, distributed, or used in any form without explicit written permission from the author. All rights are reserved.

The code, design, and implementation are protected by copyright law. Unauthorized use, copying, or distribution of this project or any of its components is strictly prohibited and may result in legal action.

## 🆘 Support

For support and questions:

- Create an issue in the repository
- Check the API documentation at `/swagger/`
- Review the Django REST Framework documentation

## 🔄 Version History

- **v1.0.0**: Initial release with basic CRUD operations
- Added JWT authentication
- Added syntax highlighting
- Added API documentation
- Added password reset functionality