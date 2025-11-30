#!/usr/bin/env python3
"""Script to create a superadmin user."""
import sys
from app import app, db
from models import User

def create_superadmin(email, password, username="Super Admin"):
    with app.app_context():
        existing = User.query.filter_by(email=email).first()
        if existing:
            print(f"User with email {email} already exists.")
            if existing.role != 'superadmin':
                existing.role = 'superadmin'
                db.session.commit()
                print(f"Updated {email} to superadmin role.")
            return
        
        user = User(
            username=username,
            email=email,
            role='superadmin'
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        print(f"Superadmin created: {email}")

if __name__ == "__main__":
    email = "admin@adscreen.com"
    password = "admin123"
    
    if len(sys.argv) >= 3:
        email = sys.argv[1]
        password = sys.argv[2]
    
    create_superadmin(email, password)
