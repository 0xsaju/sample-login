from flask import Flask, request, redirect, url_for, session, flash, jsonify
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
from werkzeug.security import generate_password_hash, check_password_hash
# from flask_wtf.csrf import CSRFProtect
import secrets
from datetime import datetime, timedelta
from flask_mail import Mail, Message
import hashlib
import os
from werkzeug.utils import secure_filename  # Add at the top with other imports
from dotenv import load_dotenv
load_dotenv()  # Add this near the top of the file
from flask_cors import CORS

app = Flask(__name__)

# Secret key for session management
app.secret_key = 'your-secret-key-here'  # Change this to a secure random string

# CSRF protection
# csrf = CSRFProtect(app)

# Enhanced security configurations
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=30)
)

# MySQL configurations
app.config.update(
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'host.docker.internal'),
    MYSQL_USER = os.getenv('MYSQL_USER', 'root'),
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', ''),
    MYSQL_DB = os.getenv('MYSQL_DB', 'sample_login')
)

mysql = MySQL(app)

# Email configuration
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = 587,
    MAIL_USERNAME = os.getenv('MAIL_USERNAME'),
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD'),
    MAIL_USE_TLS = True,
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_USERNAME')
)
mail = Mail(app)

# File upload configuration
UPLOAD_FOLDER = os.path.join('static', 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

CORS(app, supports_credentials=True)

def send_verification_email(email, token):
    try:
        msg = Message('Verify Your Email',
                      sender=os.getenv('MAIL_USERNAME'),
                      recipients=[email])
        verification_url = url_for('verify_email', token=token, _external=True)
        msg.body = f'Please click the following link to verify your email: {verification_url}'
        print(f"Attempting to send email to {email} with verification URL: {verification_url}")  # Debug log
        mail.send(msg)
        print("Email sent successfully")  # Debug log
    except Exception as e:
        print(f"Error sending email: {str(e)}")  # Debug log
        raise  # Re-raise the exception after logging

def send_reset_email(email, token):
    msg = Message('Password Reset Request',
                  sender=os.getenv('MAIL_USERNAME'),  # Use environment variable
                  recipients=[email])
    reset_url = url_for('reset_password', token=token, _external=True)
    msg.body = f'To reset your password, click the following link: {reset_url}'
    mail.send(msg)

@app.route('/register', methods=['POST'])
def register():
    cursor = None
    try:
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        # Password validation
        if not re.match(r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$', password):
            return jsonify({'success': False, 'message': 'Password must be at least 8 characters and contain letters, numbers, and special characters'}), 400
        cursor = mysql.connection.cursor()
        # Check if email exists
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': 'Email already registered'}), 400
        # Check if username exists
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': 'Username already taken'}), 400
        hashed_password = generate_password_hash(password)
        verification_token = secrets.token_urlsafe(32)
        cursor.execute('INSERT INTO users (username, email, password, verification_token) VALUES (%s, %s, %s, %s)',
                     (username, email, hashed_password, verification_token))
        mysql.connection.commit()
        try:
            send_verification_email(email, verification_token)
            msg = 'Please check your email to verify your account'
        except Exception as e:
            msg = 'Registration successful but failed to send verification email. Please contact support.'
        return jsonify({'success': True, 'message': msg}), 201
    except Exception as e:
        print(f"Registration error: {str(e)}")  # Debug log
        return jsonify({'success': False, 'message': 'An error occurred during registration'}), 500
    finally:
        if cursor:
            cursor.close()

@app.route('/verify/<token>')
def verify_email(token):
    cursor = mysql.connection.cursor()
    cursor.execute('UPDATE users SET email_verified = TRUE, verification_token = NULL WHERE verification_token = %s', (token,))
    if cursor.rowcount > 0:
        mysql.connection.commit()
        msg = 'Email verified successfully'
        success = True
    else:
        msg = 'Invalid verification token'
        success = False
    cursor.close()
    return jsonify({'success': success, 'message': msg})

@app.route('/forgot-password', methods=['POST'])
def forgot_password():
    email = request.form['email']
    cursor = mysql.connection.cursor()
    
    # First check if email exists
    cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
    user = cursor.fetchone()
    
    if user:
        reset_token = secrets.token_urlsafe(32)
        reset_expires = datetime.now() + timedelta(hours=1)
        
        cursor.execute('UPDATE users SET reset_token = %s, reset_token_expires = %s WHERE email = %s',
                      (reset_token, reset_expires, email))
        mysql.connection.commit()
        
        try:
            send_reset_email(email, reset_token)
            msg = 'Password reset instructions sent to your email'
        except Exception as e:
            msg = 'Error sending email. Please try again later.'
    else:
        msg = 'No account found with this email address'
    
    cursor.close()
    return jsonify({'success': True, 'message': msg}), 200

def add_to_password_history(user_id, password_hash):
    cursor = mysql.connection.cursor()
    cursor.execute('INSERT INTO password_history (user_id, password_hash) VALUES (%s, %s)',
                  (user_id, password_hash))
    mysql.connection.commit()
    cursor.close()

def is_password_used_before(user_id, password):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT password_hash FROM password_history WHERE user_id = %s ORDER BY created_at DESC LIMIT 5',
                  (user_id,))
    previous_passwords = cursor.fetchall()
    cursor.close()
    
    return any(check_password_hash(prev['password_hash'], password) for prev in previous_passwords)

@app.route('/change-password', methods=['POST'])
def change_password():
    if 'loggedin' not in session:
        return redirect(url_for('login'))
        
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    
    if not current_password or not new_password:
        flash('Please fill all fields', 'error')
        return redirect(url_for('profile_settings'))
        
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM users WHERE id = %s', (session['id'],))
    user = cursor.fetchone()
    
    if not check_password_hash(user['password'], current_password):
        flash('Current password is incorrect', 'error')
        return redirect(url_for('profile_settings'))
    
    if check_password_hash(user['password'], new_password):
        flash('New password must be different from current password', 'error')
        return redirect(url_for('profile_settings'))
        
    if is_password_used_before(session['id'], new_password):
        flash('This password has been used before. Please choose a different one', 'error')
        return redirect(url_for('profile_settings'))
    
    # Update password
    hashed_password = generate_password_hash(new_password)
    cursor.execute('UPDATE users SET password = %s WHERE id = %s',
                  (hashed_password, session['id']))
    
    # Add to password history
    add_to_password_history(session['id'], hashed_password)
    
    mysql.connection.commit()
    cursor.close()
    flash('Password updated successfully', 'success')
    return redirect(url_for('profile_settings'))

@app.route('/reset-password/<token>', methods=['POST'])
def reset_password(token):
    password = request.form['password']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        cursor.execute('SELECT id, password FROM users WHERE reset_token = %s AND reset_token_expires > NOW()', (token,))
        user = cursor.fetchone()
        if not user:
            return jsonify({'success': False, 'message': 'Invalid or expired reset token'}), 400
        if check_password_hash(user['password'], password):
            return jsonify({'success': False, 'message': 'New password must be different from current password'}), 400
        if is_password_used_before(user['id'], password):
            return jsonify({'success': False, 'message': 'This password has been used before. Please choose a different one'}), 400
        hashed_password = generate_password_hash(password)
        cursor.execute('''
            UPDATE users 
            SET password = %s, reset_token = NULL, reset_token_expires = NULL 
            WHERE id = %s
        ''', (hashed_password, user['id']))
        add_to_password_history(user['id'], hashed_password)
        mysql.connection.commit()
        return jsonify({'success': True, 'message': 'Password updated successfully'}), 200
    except Exception as e:
        print(f"Password reset error: {str(e)}")
        mysql.connection.rollback()
        return jsonify({'success': False, 'message': 'An error occurred during password reset'}), 500
    finally:
        cursor.close()
    # No HTML rendering in API mode
    return jsonify({'success': False, 'message': 'Invalid request method'}), 405

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    if username and password:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        account = cursor.fetchone()
        cursor.close()
        if account and check_password_hash(account['password'], password):
            if not account['email_verified']:
                return jsonify({'success': False, 'message': 'Please verify your email first'}), 403
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            return jsonify({'success': True, 'message': 'Login successful'}), 200
        else:
            return jsonify({'success': False, 'message': 'Incorrect username/password!'}), 401
    else:
        return jsonify({'success': False, 'message': 'Please fill both username and password'}), 400

def calculate_profile_completion(user):
    # Fields to check for completion
    fields = ['first_name', 'last_name', 'phone', 'country', 'bio', 'avatar_url']
    total_fields = len(fields)
    completed_fields = sum(1 for field in fields if user.get(field))
    return int((completed_fields / total_fields) * 100)

@app.route('/welcome')
def welcome():
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE id = %s', (session['id'],))
        user = cursor.fetchone()
        cursor.close()
        profile_completion = calculate_profile_completion(user)
        return jsonify({'success': True, 'username': session['username'], 'profile_completion': profile_completion})
    return jsonify({'success': False, 'message': 'Not logged in'}), 401

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return jsonify({'success': True, 'message': 'Logged out'})

@app.route('/profile')
def profile():
    if 'loggedin' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM users WHERE id = %s', (session['id'],))
    user = cursor.fetchone()
    cursor.close()
    return jsonify({'success': True, 'user': user})

@app.route('/profile/settings', methods=['POST'])
def profile_settings():
    if 'loggedin' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    try:
        first_name = request.form.get('first_name', '')
        last_name = request.form.get('last_name', '')
        phone = request.form.get('phone', '')
        country = request.form.get('country', '')
        bio = request.form.get('bio', '')
        avatar_url = None
        if 'avatar' in request.files:
            avatar = request.files['avatar']
            if avatar and avatar.filename:
                if not os.path.exists(app.config['UPLOAD_FOLDER']):
                    os.makedirs(app.config['UPLOAD_FOLDER'])
                filename = secure_filename(f"{session['username']}_{avatar.filename}")
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                avatar.save(filepath)
                avatar_url = url_for('static', filename=f'uploads/{filename}')
        if avatar_url:
            cursor.execute('''
                UPDATE users 
                SET first_name = %s, last_name = %s, phone = %s, 
                    country = %s, bio = %s, avatar_url = %s 
                WHERE id = %s
            ''', (first_name, last_name, phone, country, bio, avatar_url, session['id']))
        else:
            cursor.execute('''
                UPDATE users 
                SET first_name = %s, last_name = %s, phone = %s, 
                    country = %s, bio = %s
                WHERE id = %s
            ''', (first_name, last_name, phone, country, bio, session['id']))
        mysql.connection.commit()
        # Fetch updated user
        cursor.execute('SELECT * FROM users WHERE id = %s', (session['id'],))
        user = cursor.fetchone()
        return jsonify({'success': True, 'message': 'Profile updated successfully', 'user': user})
    except Exception as e:
        print(f"Error updating profile: {str(e)}")
        mysql.connection.rollback()
        return jsonify({'success': False, 'message': 'An error occurred while updating your profile'}), 500
    finally:
        cursor.close()

@app.errorhandler(400)
def bad_request(error):
    return jsonify({'success': False, 'message': 'Bad request'}), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'message': 'Not found'}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({'success': False, 'message': 'Server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
