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
        Content, Booking, Filler, InternalContent, StatLog, HeartbeatLog,
        SiteSetting, RegistrationRequest, ScreenOverlay, Invoice, PaymentProof,
        Broadcast
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
            country='FR',
            city='Paris',
            currency='EUR',
            timezone='Europe/Paris',
            commission_rate=10.0,
            subscription_plan='premium',
            business_name='SAS Le Bistrot Parisien',
            registration_number_label='SIRET',
            business_registration_number='123 456 789 00012'
        )
        db.session.add(org1)
        
        org2 = Organization(
            name='Bar Le Central',
            email='contact@bar-lyon.fr',
            phone='+33 4 72 00 00 00',
            address='45 Rue de la République, 69002 Lyon',
            country='FR',
            city='Lyon',
            currency='EUR',
            timezone='Europe/Paris',
            commission_rate=12.0,
            subscription_plan='basic',
            registration_number_label='SIRET'
        )
        db.session.add(org2)
        
        org3 = Organization(
            name='Centre Commercial Atlantis',
            email='pub@atlantis-mall.fr',
            phone='+33 2 40 00 00 00',
            address='Boulevard Salvador Allende, 44800 Saint-Herblain',
            country='FR',
            city='Nantes',
            currency='EUR',
            timezone='Europe/Paris',
            commission_rate=8.0,
            subscription_plan='enterprise',
            business_name='SA Atlantis Commerce',
            registration_number_label='SIRET',
            business_registration_number='987 654 321 00098'
        )
        db.session.add(org3)
        
        org4 = Organization(
            name='Café Marrakech',
            email='contact@cafe-marrakech.ma',
            phone='+212 5 24 00 00 00',
            address='Avenue Mohammed V, Guéliz, Marrakech',
            country='MA',
            city='Marrakech',
            currency='MAD',
            timezone='Africa/Casablanca',
            commission_rate=10.0,
            subscription_plan='premium',
            registration_number_label='ICE',
            business_registration_number='001234567890123'
        )
        db.session.add(org4)
        
        org5 = Organization(
            name='Restaurant Dakar Beach',
            email='info@dakar-beach.sn',
            phone='+221 33 820 00 00',
            address='Corniche Ouest, Almadies, Dakar',
            country='SN',
            city='Dakar',
            currency='XOF',
            timezone='Africa/Dakar',
            commission_rate=12.0,
            subscription_plan='basic',
            registration_number_label='NINEA'
        )
        db.session.add(org5)
        
        org6 = Organization(
            name='Tunisian Café',
            email='contact@tunis-cafe.tn',
            phone='+216 71 00 00 00',
            address='Avenue Habib Bourguiba, Tunis',
            country='TN',
            city='Tunis',
            currency='TND',
            timezone='Africa/Tunis',
            commission_rate=10.0,
            subscription_plan='basic',
            registration_number_label='Matricule Fiscal',
            business_registration_number='1234567/A/B/C/000'
        )
        db.session.add(org6)
        
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
        
        user4 = User(
            username='Café Marrakech',
            email='manager@cafe-marrakech.ma',
            role='org',
            organization_id=org4.id
        )
        user4.set_password('demo123')
        db.session.add(user4)
        
        user5 = User(
            username='Dakar Beach',
            email='manager@dakar-beach.sn',
            role='org',
            organization_id=org5.id
        )
        user5.set_password('demo123')
        db.session.add(user5)
        
        user6 = User(
            username='Tunis Café',
            email='manager@tunis-cafe.tn',
            role='org',
            organization_id=org6.id
        )
        user6.set_password('demo123')
        db.session.add(user6)
        
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
            price_per_minute=2.0,
            is_featured=True,
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
            price_per_minute=1.5,
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
            price_per_minute=1.8,
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
            price_per_minute=3.0,
            is_featured=True,
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
            price_per_minute=5.0,
            organization_id=org3.id
        )
        screen5.set_password('screen123')
        db.session.add(screen5)
        
        screen6 = Screen(
            name='Écran Terrasse Marrakech',
            location='Terrasse principale',
            latitude=31.6295,
            longitude=-7.9811,
            resolution_width=1920,
            resolution_height=1080,
            orientation='landscape',
            accepts_images=True,
            accepts_videos=True,
            max_file_size_mb=50,
            price_per_minute=20.0,
            is_featured=True,
            organization_id=org4.id
        )
        screen6.set_password('screen123')
        db.session.add(screen6)
        
        screen7 = Screen(
            name='Totem Médina',
            location='Entrée Médina',
            latitude=31.6295,
            longitude=-7.9811,
            resolution_width=1080,
            resolution_height=1920,
            orientation='portrait',
            accepts_images=True,
            accepts_videos=True,
            max_file_size_mb=50,
            price_per_minute=15.0,
            organization_id=org4.id
        )
        screen7.set_password('screen123')
        db.session.add(screen7)
        
        screen8 = Screen(
            name='Écran Beach Bar',
            location='Bar de plage',
            latitude=14.7167,
            longitude=-17.4677,
            resolution_width=1920,
            resolution_height=1080,
            orientation='landscape',
            accepts_images=True,
            accepts_videos=True,
            max_file_size_mb=50,
            price_per_minute=1000.0,
            is_featured=True,
            organization_id=org5.id
        )
        screen8.set_password('screen123')
        db.session.add(screen8)
        
        screen9 = Screen(
            name='Écran Café Habib',
            location='Salle principale',
            latitude=36.8065,
            longitude=10.1815,
            resolution_width=1920,
            resolution_height=1080,
            orientation='landscape',
            accepts_images=True,
            accepts_videos=True,
            max_file_size_mb=50,
            price_per_minute=3.0,
            is_featured=True,
            organization_id=org6.id
        )
        screen9.set_password('screen123')
        db.session.add(screen9)
        
        db.session.flush()
        
        all_screens = [screen1, screen2, screen3, screen4, screen5, screen6, screen7, screen8, screen9]
        
        logger.info("⏱️  Création des créneaux horaires (prix auto-calculés)...")
        
        for screen in all_screens:
            slot_durations = [
                ('image', 10),
                ('image', 15),
                ('image', 30),
                ('video', 15),
                ('video', 30),
                ('video', 60),
            ]
            
            for content_type, duration in slot_durations:
                if content_type == 'video' and not screen.accepts_videos:
                    continue
                calculated_price = screen.calculate_slot_price(duration)
                slot = TimeSlot(
                    content_type=content_type,
                    duration_seconds=duration,
                    price_per_play=calculated_price,
                    screen_id=screen.id
                )
                db.session.add(slot)
        
        logger.info("🕐 Création des périodes horaires...")
        
        for screen in all_screens:
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
            ('platform_business_name', 'Shabaka InnovLab SAS', 'string', 'platform'),
            ('platform_registration_number', '123 456 789 00012', 'string', 'platform'),
            ('platform_vat_number', 'FR12345678901', 'string', 'platform'),
            ('platform_vat_rate', '20.0', 'float', 'platform'),
            ('platform_timezone', 'Europe/Paris', 'string', 'platform'),
            ('registration_number_label', "Numéro d'immatriculation", 'string', 'platform'),
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
        
        for screen in all_screens:
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
            message='Bienvenue au Bistrot Parisien - Happy Hour de 17h à 19h! Cocktails à 5€',
            position='footer',
            position_mode='linear',
            background_color='#1f2937',
            text_color='#ffffff',
            font_size=28,
            scroll_speed=60,
            frequency_type='duration',
            display_duration=15,
            frequency_unit='day',
            is_active=True
        )
        db.session.add(overlay1)
        
        overlay2 = ScreenOverlay(
            screen_id=screen4.id,
            overlay_type='ticker',
            message='Centre Commercial Atlantis - Soldes jusqu\'à -50% dans toutes les boutiques! Ouvert 7j/7',
            position='header',
            position_mode='linear',
            background_color='#059669',
            text_color='#ffffff',
            font_size=32,
            scroll_speed=50,
            frequency_type='passage',
            passage_limit=20,
            frequency_unit='day',
            is_active=True
        )
        db.session.add(overlay2)
        
        overlay3 = ScreenOverlay(
            screen_id=screen2.id,
            overlay_type='ticker',
            message='Menu du jour : Plat + Dessert à 14.90€ - Réservations au 01 42 00 00 00',
            position='body',
            position_mode='linear',
            background_color='#7c3aed',
            text_color='#ffffff',
            font_size=24,
            scroll_speed=70,
            frequency_type='duration',
            display_duration=12,
            frequency_unit='noon',
            is_active=True
        )
        db.session.add(overlay3)
        
        overlay4 = ScreenOverlay(
            screen_id=screen5.id,
            overlay_type='ticker',
            message='Nouveau ! Espace restauration ouvert jusqu\'à 22h - WiFi gratuit dans tout le centre',
            position='footer',
            position_mode='linear',
            background_color='#0891b2',
            text_color='#ffffff',
            font_size=36,
            scroll_speed=55,
            frequency_type='passage',
            passage_limit=15,
            frequency_unit='evening',
            is_active=True
        )
        db.session.add(overlay4)
        
        overlay5 = ScreenOverlay(
            screen_id=screen6.id,
            overlay_type='ticker',
            message='مرحبا بكم في مقهى مراكش - Bienvenue au Café Marrakech - Thé à la menthe offert!',
            position='footer',
            position_mode='linear',
            background_color='#dc2626',
            text_color='#ffffff',
            font_size=28,
            scroll_speed=60,
            frequency_type='duration',
            display_duration=15,
            frequency_unit='day',
            is_active=True
        )
        db.session.add(overlay5)
        
        overlay6 = ScreenOverlay(
            screen_id=screen8.id,
            overlay_type='ticker',
            message='Teranga Beach Bar - Happy Hour 17h-20h - Cocktails à 2000 FCFA',
            position='header',
            position_mode='linear',
            background_color='#059669',
            text_color='#ffffff',
            font_size=28,
            scroll_speed=55,
            frequency_type='duration',
            display_duration=20,
            frequency_unit='day',
            is_active=True
        )
        db.session.add(overlay6)
        
        overlay7 = ScreenOverlay(
            screen_id=screen9.id,
            overlay_type='ticker',
            message='Café Habib Bourguiba - Wifi gratuit - Narguilé premium disponible',
            position='footer',
            position_mode='linear',
            background_color='#7c3aed',
            text_color='#ffffff',
            font_size=26,
            scroll_speed=50,
            frequency_type='passage',
            passage_limit=25,
            frequency_unit='day',
            is_active=True
        )
        db.session.add(overlay7)
        
        logger.info("📡 Création des diffusions (broadcasts) de démonstration...")
        
        broadcast1 = Broadcast(
            name='Promotion Été France',
            target_type='country',
            target_country='FR',
            broadcast_type='overlay',
            overlay_type='ticker',
            overlay_message='🌞 Soldes d\'été -30% sur toutes les publicités! Réservez maintenant!',
            overlay_position='header',
            overlay_background_color='#f97316',
            overlay_text_color='#ffffff',
            overlay_font_size=28,
            overlay_scroll_speed=60,
            is_active=True,
            created_by=superadmin.id
        )
        db.session.add(broadcast1)
        
        broadcast2 = Broadcast(
            name='Message Marrakech',
            target_type='city',
            target_country='MA',
            target_city='Marrakech',
            broadcast_type='overlay',
            overlay_type='ticker',
            overlay_message='مراكش ترحب بكم - Marrakech vous accueille! Festival des arts 2024',
            overlay_position='footer',
            overlay_background_color='#dc2626',
            overlay_text_color='#ffffff',
            overlay_font_size=26,
            overlay_scroll_speed=50,
            is_active=True,
            created_by=superadmin.id
        )
        db.session.add(broadcast2)
        
        broadcast3 = Broadcast(
            name='Promo Centre Atlantis',
            target_type='organization',
            target_organization_id=org3.id,
            broadcast_type='overlay',
            overlay_type='ticker',
            overlay_message='Centre Commercial Atlantis - Nouveau magasin Apple ouvert! Venez découvrir.',
            overlay_position='body',
            overlay_background_color='#2563eb',
            overlay_text_color='#ffffff',
            overlay_font_size=30,
            overlay_scroll_speed=55,
            is_active=True,
            created_by=superadmin.id
        )
        db.session.add(broadcast3)
        
        broadcast4 = Broadcast(
            name='Info Écran Beach',
            target_type='screen',
            target_screen_id=screen8.id,
            broadcast_type='overlay',
            overlay_type='ticker',
            overlay_message='🏖️ Soirée spéciale ce soir! DJ set à partir de 20h - Teranga Beach Bar',
            overlay_position='header',
            overlay_background_color='#16a34a',
            overlay_text_color='#ffffff',
            overlay_font_size=24,
            overlay_scroll_speed=65,
            is_active=True,
            created_by=superadmin.id
        )
        db.session.add(broadcast4)
        
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
    
    🏢 ÉTABLISSEMENTS (mot de passe: demo123):
    
    🇫🇷 FRANCE (EUR):
       1️⃣  Le Bistrot Parisien - manager@restaurant-paris.fr
       2️⃣  Bar Le Central - manager@bar-lyon.fr
       3️⃣  Centre Commercial Atlantis - manager@atlantis-mall.fr
    
    🇲🇦 MAROC (MAD):
       4️⃣  Café Marrakech - manager@cafe-marrakech.ma
    
    🇸🇳 SÉNÉGAL (XOF):
       5️⃣  Restaurant Dakar Beach - manager@dakar-beach.sn
    
    🇹🇳 TUNISIE (TND):
       6️⃣  Tunisian Café - manager@tunis-cafe.tn
    
    📺 ÉCRANS (mot de passe player: screen123):
       • Le Bistrot Parisien: 2 écrans (FR)
       • Bar Le Central: 1 écran (FR)
       • Centre Commercial Atlantis: 2 écrans (FR)
       • Café Marrakech: 2 écrans (MA)
       • Restaurant Dakar Beach: 1 écran (SN)
       • Tunisian Café: 1 écran (TN)
    
    🔲 OVERLAYS DE DÉMONSTRATION (7 bandeaux):
       • Écran Entrée (footer) - Happy Hour
       • Totem Hall A (header) - Soldes
       • Écran Bar (body) - Menu du jour
       • Écran Food Court (footer) - Horaires
       • Terrasse Marrakech (footer) - Bilingue AR/FR
       • Beach Bar Dakar (header) - Happy Hour FCFA
       • Café Habib Tunis (footer) - Services
    
    📡 DIFFUSIONS (BROADCASTS) DE DÉMONSTRATION (4):
       • Promotion Été France (pays: FR) - Bandeau header
       • Message Marrakech (ville: Marrakech) - Bandeau footer
       • Promo Centre Atlantis (établissement) - Bandeau body
       • Info Écran Beach (écran spécifique) - Bandeau header
    
    ════════════════════════════════════════════════════════════════
        """)
        
        return True


def clear_demo_data():
    """🗑️ Supprime toutes les données de démonstration."""
    from app import app, db
    from sqlalchemy import text
    
    with app.app_context():
        logger.warning("⚠️  Suppression de toutes les données...")
        
        # Drop tables in correct order to avoid circular dependency
        tables_to_drop = [
            'broadcasts', 'payment_proofs', 'invoices',
            'stat_logs', 'heartbeat_logs', 'screen_overlays',
            'contents', 'bookings', 'fillers', 'internal_contents',
            'time_slots', 'time_periods', 'screens',
            'registration_requests', 'site_settings',
            'users', 'organizations'
        ]
        
        for table in tables_to_drop:
            try:
                db.session.execute(text(f'DROP TABLE IF EXISTS {table} CASCADE'))
            except Exception as e:
                logger.debug(f"Table {table}: {e}")
        
        db.session.commit()
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
