#!/usr/bin/env python3
"""
🎮 Script de création des données de démonstration Shabaka AdScreen
📌 Crée des comptes et données exemple pour tester l'application.
"""
import sys
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_demo_data():
    """🎭 Crée les données de démonstration."""
    from app import app, db
    from models import (
        User, Organization, Screen, TimeSlot, TimePeriod,
        Filler, InternalContent, SiteSetting, ScreenOverlay
    )
    
    with app.app_context():
        db.create_all()
        
        existing_admin = User.query.filter_by(email='admin@shabaka-adscreen.com').first()
        if existing_admin:
            logger.warning("⚠️  Les données de démonstration existent déjà.")
            logger.info("💡 Utilisez --force pour les recréer.")
            return True
        
        logger.info("👑 Création du superadmin...")
        superadmin = User(
            username='Super Admin',
            email='admin@shabaka-adscreen.com',
            role='superadmin'
        )
        superadmin.set_password('admin123')
        db.session.add(superadmin)
        
        logger.info("🏢 Création des organisations...")
        
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
        
        logger.info("👥 Création des utilisateurs établissement...")
        
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
        
        logger.info("📺 Création des écrans...")
        
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
        
        logger.info("⏱️  Création des créneaux horaires...")
        
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
        
        logger.info("🕐 Création des périodes horaires...")
        
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
        
        logger.info("⚙️  Configuration des paramètres du site...")
        
        site_settings = [
            ('platform_name', 'Shabaka AdScreen', 'string', 'platform'),
            ('support_email', 'support@shabaka-adscreen.com', 'string', 'platform'),
            ('admin_whatsapp_number', '33612345678', 'string', 'platform'),
            ('default_commission_rate', '10.0', 'float', 'platform'),
            ('min_commission_rate', '5.0', 'float', 'platform'),
            ('max_commission_rate', '30.0', 'float', 'platform'),
            ('maintenance_mode', 'false', 'boolean', 'platform'),
            ('site_title', 'Shabaka AdScreen - Location Écrans Publicitaires', 'string', 'seo'),
            ('site_description', 'Un Produit de Shabaka InnovLab - Plateforme de location d\'espaces publicitaires sur écrans', 'string', 'seo'),
        ]
        
        for key, value, value_type, category in site_settings:
            SiteSetting.set(key, value, value_type, category)
        
        logger.info("🎨 Création des fillers par défaut pour chaque écran...")
        
        from services.filler_generator import generate_default_filler
        import os as file_os
        
        platform_name = SiteSetting.get('platform_name', 'Shabaka AdScreen')
        platform_url = 'www.shabaka-adscreen.com'
        
        base_url = file_os.environ.get('REPLIT_DEV_DOMAIN', '')
        if base_url:
            base_url = f"https://{base_url}"
        else:
            base_url = None
        
        for screen in [screen1, screen2, screen3, screen4, screen5]:
            org_id = screen.organization_id
            upload_dir = f"static/uploads/fillers/{org_id}"
            file_os.makedirs(upload_dir, exist_ok=True)
            
            img_data, filename = generate_default_filler(
                screen, 
                platform_name=platform_name, 
                platform_url=platform_url,
                base_url=base_url
            )
            
            file_path = file_os.path.join(upload_dir, filename)
            with open(file_path, 'wb') as f:
                f.write(img_data)
            
            filler = Filler(
                filename=filename,
                content_type='image',
                file_path=file_path,
                duration_seconds=10.0,
                is_active=True,
                in_playlist=True,
                screen_id=screen.id
            )
            db.session.add(filler)
        
        db.session.flush()
        
        logger.info("🔲 Création des overlays de démonstration...")
        
        overlay1 = ScreenOverlay(
            screen_id=screen1.id,
            overlay_type='ticker',
            message='Bienvenue au Bistrot Parisien - Happy Hour de 17h à 19h!',
            position='footer',
            background_color='#1f2937',
            text_color='#ffffff',
            font_size=28,
            scroll_speed=60,
            is_active=True
        )
        db.session.add(overlay1)
        
        overlay2 = ScreenOverlay(
            screen_id=screen4.id,
            overlay_type='ticker',
            message='Centre Commercial Atlantis - Soldes jusqu\'à -50% dans toutes les boutiques!',
            position='header',
            background_color='#059669',
            text_color='#ffffff',
            font_size=32,
            scroll_speed=50,
            is_active=True
        )
        db.session.add(overlay2)
        
        db.session.commit()
        
        print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║  🎉 DONNÉES DE DÉMONSTRATION CRÉÉES AVEC SUCCÈS! 🎉          ║
    ╚═══════════════════════════════════════════════════════════════╝
    
    👤 COMPTES CRÉÉS:
    ════════════════════════════════════════════════════════════════
    
    👑 SUPERADMIN:
       📧 Email: admin@shabaka-adscreen.com
       🔑 Mot de passe: admin123
    
    🏢 ÉTABLISSEMENTS:
    
       1️⃣  Le Bistrot Parisien
          📧 Email: manager@restaurant-paris.fr
          🔑 Mot de passe: demo123
    
       2️⃣  Bar Le Central
          📧 Email: manager@bar-lyon.fr
          🔑 Mot de passe: demo123
    
       3️⃣  Centre Commercial Atlantis
          📧 Email: manager@atlantis-mall.fr
          🔑 Mot de passe: demo123
    
    📺 ÉCRANS (mot de passe player: screen123):
       • Le Bistrot Parisien: 2 écrans
       • Bar Le Central: 1 écran
       • Centre Commercial Atlantis: 2 écrans
    
    🔲 OVERLAYS DE DÉMONSTRATION:
       • Bandeau défilant sur Écran Entrée
       • Bandeau défilant sur Totem Hall A
    
    ════════════════════════════════════════════════════════════════
        """)
        
        return True


def clear_demo_data():
    """🗑️ Supprime toutes les données de démonstration."""
    from app import app, db
    
    with app.app_context():
        logger.warning("⚠️  Suppression de toutes les données...")
        db.drop_all()
        db.create_all()
        logger.info("✅ Base de données réinitialisée.")
    
    return True


def main():
    print("""
    ╔════════════════════════════════════════════════════════════════════╗
    ║  🎮 Shabaka AdScreen - Création des Données de Démonstration 🎭   ║
    ╚════════════════════════════════════════════════════════════════════╝
    """)
    
    import argparse
    
    parser = argparse.ArgumentParser(description='🎮 Crée les données de démonstration Shabaka AdScreen')
    parser.add_argument(
        '--force',
        action='store_true',
        help='🔄 Force la recréation des données (supprime les existantes)'
    )
    parser.add_argument(
        '--clear',
        action='store_true',
        help='🗑️ Supprime toutes les données sans en créer de nouvelles'
    )
    
    args = parser.parse_args()
    
    try:
        if args.clear:
            response = input("⚠️  ATTENTION: Toutes les données seront supprimées. Continuer ? (oui/non) : ")
            if response.lower() != 'oui':
                logger.info("🚫 Opération annulée.")
                return 0
            return 0 if clear_demo_data() else 1
        
        if args.force:
            response = input("⚠️  ATTENTION: Les données existantes seront supprimées. Continuer ? (oui/non) : ")
            if response.lower() != 'oui':
                logger.info("🚫 Opération annulée.")
                return 0
            clear_demo_data()
        
        success = create_demo_data()
        return 0 if success else 1
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la création des données : {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
