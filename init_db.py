#!/usr/bin/env python3
"""
🗄️ Script d'initialisation de la base de données Shabaka AdScreen
📌 Crée toutes les tables définies dans les modèles SQLAlchemy.
"""
import sys
import argparse
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def init_database(drop_existing=False):
    """
    🚀 Initialise la base de données.
    
    Args:
        drop_existing: Si True, supprime les tables existantes avant de les recréer
    """
    from app import app, db
    
    with app.app_context():
        if drop_existing:
            logger.warning("⚠️  Suppression de toutes les tables existantes...")
            db.drop_all()
            logger.info("🗑️  Tables supprimées.")
        
        logger.info("🔨 Création des tables...")
        db.create_all()
        logger.info("✅ Base de données initialisée avec succès!")
        
        from models import (
            User, Organization, Screen, TimeSlot, TimePeriod,
            Content, Booking, Filler, InternalContent, StatLog, HeartbeatLog,
            SiteSetting, RegistrationRequest, ScreenOverlay
        )
        
        tables = [
            ('👤 users', User),
            ('🏢 organizations', Organization),
            ('📺 screens', Screen),
            ('⏱️  time_slots', TimeSlot),
            ('🕐 time_periods', TimePeriod),
            ('🎬 contents', Content),
            ('📅 bookings', Booking),
            ('🎨 fillers', Filler),
            ('📝 internal_contents', InternalContent),
            ('📊 stat_logs', StatLog),
            ('💓 heartbeat_logs', HeartbeatLog),
            ('⚙️  site_settings', SiteSetting),
            ('📋 registration_requests', RegistrationRequest),
            ('🔲 screen_overlays', ScreenOverlay),
        ]
        
        logger.info("\n📋 Tables créées :")
        for table_name, model in tables:
            count = model.query.count()
            logger.info(f"  {table_name}: {count} enregistrements")
    
    return True


def main():
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║  🖥️  Shabaka AdScreen - Initialisation Base de Données  🗄️   ║
    ╚════════════════════════════════════════════════════════════════╝
    """)
    
    parser = argparse.ArgumentParser(description='🗄️ Initialise la base de données Shabaka AdScreen')
    parser.add_argument(
        '--drop',
        action='store_true',
        help='⚠️ Supprime les tables existantes avant de les recréer (ATTENTION: perte de données)'
    )
    parser.add_argument(
        '--check',
        action='store_true',
        help='🔍 Vérifie simplement la connexion à la base de données'
    )
    
    args = parser.parse_args()
    
    if args.check:
        try:
            from app import app, db
            with app.app_context():
                db.engine.connect()
            logger.info("✅ Connexion à la base de données réussie!")
            return 0
        except Exception as e:
            logger.error(f"❌ Erreur de connexion : {e}")
            return 1
    
    try:
        if args.drop:
            response = input("⚠️  ATTENTION: Toutes les données seront perdues. Continuer ? (oui/non) : ")
            if response.lower() != 'oui':
                logger.info("🚫 Opération annulée.")
                return 0
        
        success = init_database(drop_existing=args.drop)
        if success:
            logger.info("\n🎉 Initialisation terminée avec succès!")
        return 0 if success else 1
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'initialisation : {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
