from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from models import User, Organization

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.is_superadmin():
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('org.dashboard'))
    return render_template('index.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.is_superadmin():
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('org.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('Votre compte a été désactivé.', 'error')
                return render_template('auth/login.html')
            
            login_user(user)
            next_page = request.args.get('next')
            
            if user.is_superadmin():
                return redirect(next_page or url_for('admin.dashboard'))
            return redirect(next_page or url_for('org.dashboard'))
        
        flash('Email ou mot de passe incorrect.', 'error')
    
    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('org.dashboard'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        org_name = request.form.get('org_name')
        phone = request.form.get('phone')
        address = request.form.get('address')
        
        if password != confirm_password:
            flash('Les mots de passe ne correspondent pas.', 'error')
            return render_template('auth/register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Cet email est déjà utilisé.', 'error')
            return render_template('auth/register.html')
        
        org = Organization(
            name=org_name,
            email=email,
            phone=phone,
            address=address
        )
        db.session.add(org)
        db.session.flush()
        
        user = User(
            username=name,
            email=email,
            role='org',
            organization_id=org.id
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Compte créé avec succès! Vous pouvez maintenant vous connecter.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Vous avez été déconnecté.', 'info')
    return redirect(url_for('auth.index'))
