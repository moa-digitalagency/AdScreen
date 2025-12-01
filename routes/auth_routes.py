from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from models import User, Organization, SiteSetting, RegistrationRequest
import urllib.parse

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.is_superadmin():
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('org.dashboard'))
    
    from models import Screen
    featured_screens = Screen.query.filter_by(is_featured=True, is_active=True).join(
        Organization
    ).filter(Organization.is_active == True).limit(6).all()
    
    return render_template('index.html', featured_screens=featured_screens)


@auth_bp.route('/contact', methods=['POST'])
def contact():
    name = request.form.get('name', '')
    email = request.form.get('email', '')
    message = request.form.get('message', '')
    
    admin_whatsapp = SiteSetting.get('admin_whatsapp_number', '')
    if admin_whatsapp:
        whatsapp_message = f"""Nouveau message de contact AdScreen:

Nom: {name}
Email: {email}
Message: {message}"""
        
        encoded_message = urllib.parse.quote(whatsapp_message)
        whatsapp_url = f"https://wa.me/{admin_whatsapp}?text={encoded_message}"
        return redirect(whatsapp_url)
    
    flash('Message envoyé avec succès!', 'success')
    return redirect(url_for('auth.index'))


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
    from utils.currencies import get_all_currencies
    
    if current_user.is_authenticated:
        return redirect(url_for('org.dashboard'))
    
    currencies = get_all_currencies()
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        org_name = request.form.get('org_name')
        phone = request.form.get('phone')
        address = request.form.get('address')
        currency = request.form.get('currency', 'EUR')
        message = request.form.get('message', '')
        
        if not name or not email or not org_name or not phone:
            flash('Veuillez remplir tous les champs obligatoires.', 'error')
            return render_template('auth/register.html', currencies=currencies)
        
        existing_request = RegistrationRequest.query.filter_by(email=email, status='pending').first()
        if existing_request:
            flash('Une demande est déjà en cours pour cet email.', 'warning')
            return render_template('auth/register.html', currencies=currencies)
        
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Cet email est déjà associé à un compte.', 'error')
            return render_template('auth/register.html', currencies=currencies)
        
        reg_request = RegistrationRequest(
            name=name,
            email=email,
            org_name=org_name,
            phone=phone,
            address=address,
            currency=currency,
            message=message
        )
        db.session.add(reg_request)
        db.session.commit()
        
        admin_whatsapp = SiteSetting.get('admin_whatsapp_number', '')
        if admin_whatsapp:
            whatsapp_message = f"""Nouvelle demande d'inscription AdScreen:

Nom: {name}
Email: {email}
Établissement: {org_name}
Téléphone: {phone}
Adresse: {address or 'Non renseignée'}
Devise: {currency}
Message: {message or 'Aucun'}

Connectez-vous à l'admin pour valider cette demande."""
            
            encoded_message = urllib.parse.quote(whatsapp_message)
            whatsapp_url = f"https://wa.me/{admin_whatsapp}?text={encoded_message}"
        
        flash('Votre demande a été envoyée avec succès! Nous vous contacterons bientôt via WhatsApp.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', currencies=currencies)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Vous avez été déconnecté.', 'info')
    return redirect(url_for('auth.index'))
