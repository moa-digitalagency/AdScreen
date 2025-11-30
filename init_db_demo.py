#!/usr/bin/env python3
"""
Script de création des données de démonstration.
Crée des comptes et données exemple pour tester l'application.
"""
import sys
import logging
from datetime import datetime, date, timedelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_demo_data():
    """Crée les données de démonstration."""
    from app import app, db
    from models import (
        User, Organization, Screen, TimeSlot, TimePeriod,
        Filler, InternalContent
    )
    
    with app.app_context():
        db.create_all()
        
        existing_admin = User.query.filter_by(email='admin@adscreen.com').first()
        if existing_admin:
            logger.warning("Les données de démonstration existent déjà.")
            logger.info("Utilisez --force pour les recréer.")
            return True
        
        logger.info("Création du superadmin...")
        superadmin = User(
            username='Super Admin',
            email='admin@adscreen.com',
            role='superadmin'
        )
        superadmin.set_password('admin123')
        db.session.add(superadmin)
        
        logger.info("Création des organisations...")
        
        org1 = Organization(
            name='Le Bistrot Parisien',
            email='demo@restaurant-paris.fr',
            phone='+33 1 42 00 00 00',
            address='123 Avenue des Champs-Élysées, 75008 Paris',
            commission_rate=10.0,
            subscription_plan='premium'
        )
        db.session.add(org1)
        
        org2 = Organization(
            name='Bar Le Central',
            email='contact@bar-lyon.fr',
            phone='+33 4 72 00 00 00',
            address='45 Rue de la République, 69002 Lyon',
            commission_rate=12.0,
            subscription_plan='basic'
        )
        db.session.add(org2)
        
        org3 = Organization(
            name='Centre Commercial Atlantis',
            email='pub@atlantis-mall.fr',
            phone='+33 2 40 00 00 00',
            address='Boulevard Salvador Allende, 44800 Saint-Herblain',
            commission_rate=8.0,
            subscription_plan='enterprise'
        )
        db.session.add(org3)
        
        db.session.flush()
        
        logger.info("Création des utilisateurs établissement...")
        
        user1 = User(
            username='Restaurant Paris',
            email='manager@restaurant-paris.fr',
            role='org',
            organization_id=org1.id
        )
        user1.set_password('demo123')
        db.session.add(user1)
        
        user2 = User(
            username='Bar Lyon',
            email='manager@bar-lyon.fr',
            role='org',
            organization_id=org2.id
        )
        user2.set_password('demo123')
        db.session.add(user2)
        
        user3 = User(
            username='Atlantis Manager',
            email='manager@atlantis-mall.fr',
            role='org',
            organization_id=org3.id
        )
        user3.set_password('demo123')
        db.session.add(user3)
        
        logger.info("Création des écrans...")
        
        screen1 = Screen(
            name='Écran Entrée',
            location='Hall d\'entrée principal',
            latitude=48.8698,
            longitude=2.3076,
            resolution_width=1920,
            resolution_height=1080,
            orientation='landscape',
            accepts_images=True,
            accepts_videos=True,
            max_file_size_mb=50,
            organization_id=org1.id
        )
        screen1.set_password('screen123')
        db.session.add(screen1)
        
        screen2 = Screen(
            name='Écran Bar',
            location='Au-dessus du bar',
            latitude=48.8698,
            longitude=2.3076,
            resolution_width=1080,
            resolution_height=1920,
            orientation='portrait',
            accepts_images=True,
            accepts_videos=True,
            max_file_size_mb=30,
            organization_id=org1.id
        )
        screen2.set_password('screen123')
        db.session.add(screen2)
        
        screen3 = Screen(
            name='Écran Principal',
            location='Salle principale',
            latitude=45.7640,
            longitude=4.8357,
            resolution_width=1920,
            resolution_height=1080,
            orientation='landscape',
            accepts_images=True,
            accepts_videos=False,
            max_file_size_mb=20,
            organization_id=org2.id
        )
        screen3.set_password('screen123')
        db.session.add(screen3)
        
        screen4 = Screen(
            name='Totem Hall A',
            location='Entrée Hall A',
            latitude=47.2184,
            longitude=-1.6278,
            resolution_width=1080,
            resolution_height=1920,
            orientation='portrait',
            accepts_images=True,
            accepts_videos=True,
            max_file_size_mb=100,
            organization_id=org3.id
        )
        screen4.set_password('screen123')
        db.session.add(screen4)
        
        screen5 = Screen(
            name='Écran Géant Food Court',
            location='Zone restauration',
            latitude=47.2184,
            longitude=-1.6278,
            resolution_width=3840,
            resolution_height=2160,
            orientation='landscape',
            accepts_images=True,
            accepts_videos=True,
            max_file_size_mb=200,
            organization_id=org3.id
        )
        screen5.set_password('screen123')
        db.session.add(screen5)
        
        db.session.flush()
        
        logger.info("Création des créneaux horaires...")
        
        for screen in [screen1, screen2, screen3, screen4, screen5]:
            slots = [
                ('image', 5, 0.50),
                ('image', 10, 0.80),
                ('image', 15, 1.00),
                ('video', 10, 1.50),
                ('video', 15, 2.00),
                ('video', 30, 3.50),
            ]
            
            for content_type, duration, price in slots:
                if content_type == 'video' and not screen.accepts_videos:
                    continue
                slot = TimeSlot(
                    content_type=content_type,
                    duration_seconds=duration,
                    price_per_play=price,
                    screen_id=screen.id
                )
                db.session.add(slot)
        
        logger.info("Création des périodes horaires...")
        
        for screen in [screen1, screen2, screen3, screen4, screen5]:
            periods = [
                ('Matin', 6, 12, 0.8),
                ('Midi', 12, 14, 1.5),
                ('Après-midi', 14, 18, 1.0),
                ('Soir', 18, 22, 1.8),
                ('Nuit', 22, 6, 0.5),
            ]
            
            for name, start, end, multiplier in periods:
                period = TimePeriod(
                    name=name,
                    start_hour=start,
                    end_hour=end,
                    price_multiplier=multiplier,
                    screen_id=screen.id
                )
                db.session.add(period)
        
        db.session.commit()
        
        logger.info("\n" + "="*50)
        logger.info("DONNÉES DE DÉMONSTRATION CRÉÉES AVEC SUCCÈS")
        logger.info("="*50)
        logger.info("\nComptes créés :")
        logger.info("-"*50)
        logger.info("SUPERADMIN:")
        logger.info("  Email: admin@adscreen.com")
        logger.info("  Mot de passe: admin123")
        logger.info("")
        logger.info("ÉTABLISSEMENTS:")
        logger.info("  1. Le Bistrot Parisien")
        logger.info("     Email: manager@restaurant-paris.fr")
        logger.info("     Mot de passe: demo123")
        logger.info("")
        logger.info("  2. Bar Le Central")
        logger.info("     Email: manager@bar-lyon.fr")
        logger.info("     Mot de passe: demo123")
        logger.info("")
        logger.info("  3. Centre Commercial Atlantis")
        logger.info("     Email: manager@atlantis-mall.fr")
        logger.info("     Mot de passe: demo123")
        logger.info("")
        logger.info("ÉCRANS (mot de passe player: screen123):")
        logger.info("  - Le Bistrot Parisien: 2 écrans")
        logger.info("  - Bar Le Central: 1 écran")
        logger.info("  - Centre Commercial Atlantis: 2 écrans")
        logger.info("-"*50)
        
        return True


def clear_demo_data():
    """Supprime toutes les données de démonstration."""
    from app import app, db
    
    with app.app_context():
        logger.warning("Suppression de toutes les données...")
        db.drop_all()
        db.create_all()
        logger.info("Base de données réinitialisée.")
    
    return True


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Crée les données de démonstration AdScreen')
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force la recréation des données (supprime les existantes)'
    )
    parser.add_argument(
        '--clear',
        action='store_true',
        help='Supprime toutes les données sans en créer de nouvelles'
    )
    
    args = parser.parse_args()
    
    try:
        if args.clear:
            response = input("ATTENTION: Toutes les données seront supprimées. Continuer ? (oui/non) : ")
            if response.lower() != 'oui':
                logger.info("Opération annulée.")
                return 0
            return 0 if clear_demo_data() else 1
        
        if args.force:
            response = input("ATTENTION: Les données existantes seront supprimées. Continuer ? (oui/non) : ")
            if response.lower() != 'oui':
                logger.info("Opération annulée.")
                return 0
            clear_demo_data()
        
        success = create_demo_data()
        return 0 if success else 1
        
    except Exception as e:
        logger.error(f"Erreur lors de la création des données : {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
