from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from .models import Signupuser  
from .views import views_bp
from . import db

# Website/auth.py


auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login')
def login():
    return render_template('login.html')

@auth_bp.route('/signup')
def signup():
    return render_template('signup.html')

@auth_bp.route('/signup-user', methods=['POST'])
def signup_user():
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    hashed_password = generate_password_hash(password)

    user = Signupuser.query.filter_by(email=email).first()
    if user:
        flash('Email already exists!', 'danger')
        return render_template('signup.html')

    new_user = Signupuser(name=username, email=email, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    flash("Signup successful. Please login.", "success")
    return redirect(url_for('auth.login'))

@auth_bp.route('/login-user', methods=['POST'])
def login_user_route():
    email = request.form['email']
    password = request.form['password']
    user = Signupuser.query.filter_by(email=email).first()
    if user and check_password_hash(user.password, password):
        login_user(user)
        flash("Login Success", "success")
        return redirect(url_for('views.index'))
    else:
        flash("Invalid credentials", "danger")
        return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logged out successfully", "info")
    return redirect(url_for('auth.login'))
@auth_bp.route('/profile')
@login_required
def profile():
    return render_template('profile.html')
@auth_bp.route('/edit-profile')
@login_required
def edit_profile():
    user = Signupuser.query.get(current_user.id)
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('auth.profile'))
    return render_template('edit_profile.html', user=user)    

    return render_template('profile.html')
@auth_bp.route('/update-profile', methods=['POST', 'GET'])
@login_required
def update_profile():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        if not name or not email:
            flash('Name and Email are required.', 'warning')
            return redirect(url_for('auth.profile'))
        
        has_password = generate_password_hash(password)
        db.session.query(Signupuser).filter_by(id=current_user.id).update(
            {
                'name': name,
                'email': email,
                'password':has_password 
            }
        )
        db.session.commit()
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('auth.profile'))


