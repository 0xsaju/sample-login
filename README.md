# Modern Login System

A modern and secure login system built with Flask, featuring email verification, password reset, and profile management.

## Features

- 🔐 Secure Authentication
  - Password hashing
  - CSRF protection
  - Session management
  - Password history tracking
  - Previous password reuse prevention

- ✉️ Email Features
  - Email verification
  - Password reset via email
  - Configurable email templates

- 👤 User Management
  - Profile customization
  - Avatar upload
  - Profile completion tracking
  - Password change functionality

- 🛡️ Security Features
  - SQL injection prevention
  - XSS protection
  - Secure password policies
  - Rate limiting
  - Session timeout

## Tech Stack

- Backend: Python/Flask
- Database: MySQL
- Frontend: HTML5, CSS3
- Email: Flask-Mail
- Security: Flask-WTF, Werkzeug

## Installation

1. Clone the repository
```bash
git clone https://github.com/0xsaju/sample-login.git
cd sample-login
```

2. Create virtual environment
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Set up environment variables in `.env`
```env
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password
```

5. Initialize database
```bash
mysql -u root -p sample_login < initial.sql
```

6. Run the application
```bash
python app.py
```

## Project Structure

```
sample-login/
├── app.py                 # Main application file
├── initial.sql           # Database schema
├── requirements.txt      # Project dependencies
├── static/              # Static files
│   └── uploads/        # User uploads
└── templates/          # HTML templates
    ├── index.html     # Login page
    ├── register.html  # Registration page
    ├── profile.html   # User profile
    └── ...
```

## Configuration

- Database settings in `app.py`
- Email settings in `.env`
- File upload settings in `app.py`
- Session configuration in `app.py`

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Open a pull request

## Future Improvements

- [ ] CI/CD integration
- [ ] Docker containerization
- [ ] OAuth integration
- [ ] Two-factor authentication
- [ ] API endpoints
- [ ] Unit tests

## Author

[github.com/0xsaju](https://github.com/0xsaju)

## License

This project is licensed under the MIT License - see the LICENSE file for details
