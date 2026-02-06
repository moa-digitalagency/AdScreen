#!/usr/bin/env python3
"""
 * Nom de l'application : Shabaka AdScreen
 * Description : Script d'initialisation de la base de données (migrations auto)
 * Produit de : MOA Digital Agency, www.myoneart.com
 * Fait par : Aisance KALONJI, www.aisancekalonji.com
 * Auditer par : La CyberConfiance, www.cyberconfiance.com

Script d'initialisation de la base de données Shabaka AdScreen
Crée toutes les tables définies dans les modèles SQLAlchemy.
Ajoute automatiquement les colonnes manquantes aux tables existantes.

Usage VPS:
    python init_db.py          # Initialize/update database
    python init_db.py --check  # Verify database connection
    python init_db.py --drop   # Reset database (WARNING: data loss)
"""
import sys
import os
import argparse
import logging
from sqlalchemy import inspect, text

os.environ.setdefault('INIT_DB_MODE', 'true')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_column_type_sql(column):
    """Convertit le type SQLAlchemy en type SQL pour ALTER TABLE."""
    from sqlalchemy import Boolean, Integer, Float, String, Text, DateTime, Date, Time, Numeric, SmallInteger, LargeBinary
    from sqlalchemy.dialects.postgresql import JSON, JSONB, UUID

    col_type = type(column.type)
    
    if col_type == Boolean:
        return "BOOLEAN"
    elif col_type == Integer:
        return "INTEGER"
    elif col_type == SmallInteger:
        return "SMALLINT"
    elif col_type == Float:
        return "FLOAT"
    elif col_type == Numeric:
        precision = getattr(column.type, 'precision', None)
        scale = getattr(column.type, 'scale', None)
        if precision and scale:
            return f"NUMERIC({precision}, {scale})"
        return "NUMERIC"
    elif col_type == String:
        length = getattr(column.type, 'length', 255) or 255
        return f"VARCHAR({length})"
    elif col_type == Text:
        return "TEXT"
    elif col_type == DateTime:
        return "TIMESTAMP"
    elif col_type == Date:
        return "DATE"
    elif col_type == Time:
        return "TIME"
    elif col_type == LargeBinary:
        return "BYTEA"
    elif col_type in (JSON, JSONB):
        return "JSONB"
    elif col_type == UUID:
        return "UUID"
    else:
        return "TEXT"


def get_default_value_sql(column):
    """Récupère la valeur par défaut pour une colonne."""
    if column.default is not None:
        default = column.default.arg
        if isinstance(default, bool):
            return "TRUE" if default else "FALSE"
        elif isinstance(default, (int, float)):
            return str(default)
        elif isinstance(default, str):
            return f"'{default}'"
    return None


def sync_missing_columns(db):
    """
    Synchronise les colonnes manquantes dans les tables existantes.
    Ajoute automatiquement les colonnes définies dans les modèles mais absentes de la DB.
    """
    # Force l'import de tous les modèles pour qu'ils soient enregistrés dans db.metadata
    import models  # noqa: F401
    
    inspector = inspect(db.engine)
    existing_tables = set(inspector.get_table_names())
    
    columns_added = 0
    
    # Itérer sur toutes les tables définies dans SQLAlchemy
    for table_name, table in db.metadata.tables.items():
        if table_name not in existing_tables:
            continue

        existing_columns = {col['name'] for col in inspector.get_columns(table_name)}
        
        for col_name, column in table.columns.items():
            if col_name not in existing_columns:
                col_type = get_column_type_sql(column)
                default_sql = get_default_value_sql(column)
                
                # Check dialect to use appropriate syntax
                is_sqlite = db.engine.dialect.name == 'sqlite'

                if is_sqlite:
                    # SQLite does not support IF NOT EXISTS for columns
                    alter_sql = f'ALTER TABLE "{table_name}" ADD COLUMN "{col_name}" {col_type}'
                else:
                    # Postgres and others usually support IF NOT EXISTS
                    alter_sql = f'ALTER TABLE "{table_name}" ADD COLUMN IF NOT EXISTS "{col_name}" {col_type}'
                
                if default_sql:
                    alter_sql += f" DEFAULT {default_sql}"
                
                try:
                    db.session.execute(text(alter_sql))
                    db.session.commit()
                    logger.info(f"  + Colonne ajoutée: {table_name}.{col_name} ({col_type})")
                    columns_added += 1
                except Exception as e:
                    logger.warning(f"  ! Impossible d'ajouter {table_name}.{col_name}: {e}")
                    db.session.rollback()
    
    return columns_added


def init_database(drop_existing=False):
    """
    Initialise la base de données.
    
    Args:
        drop_existing: Si True, supprime les tables existantes avant de les recréer
    """
    from app import app, db
    
    with app.app_context():
        if drop_existing:
            logger.warning("Suppression de toutes les tables existantes...")
            db.drop_all()
            logger.info("Tables supprimées.")
        
        logger.info("Création des tables...")
        db.create_all()
        logger.info("Tables de base créées.")
        
        logger.info("Synchronisation des colonnes manquantes...")
        columns_added = sync_missing_columns(db)
        if columns_added > 0:
            logger.info(f"{columns_added} colonne(s) ajoutée(s).")
        else:
            logger.info("Toutes les colonnes sont à jour.")
        
        logger.info("Base de données initialisée avec succès!")
        
        # Récapitulatif dynamique
        logger.info("\nTables vérifiées :")
        for table_name in db.metadata.tables.keys():
            try:
                # On utilise directement SQL pour compter pour éviter d'avoir besoin des classes Model importées spécifiquement
                result = db.session.execute(text(f'SELECT COUNT(*) FROM "{table_name}"'))
                count = result.scalar()
                logger.info(f"  {table_name}: {count} enregistrements")
            except Exception as e:
                logger.warning(f"  {table_name}: erreur de lecture - {e}")
    
    return True


def main():
    print("""
    ╔════════════════════════════════════════════════════════════════╗
    ║     Shabaka AdScreen - Initialisation Base de Données         ║
    ╚════════════════════════════════════════════════════════════════╝
    """)
    
    parser = argparse.ArgumentParser(description='Initialise la base de données Shabaka AdScreen')
    parser.add_argument(
        '--drop',
        action='store_true',
        help='Supprime les tables existantes avant de les recréer (ATTENTION: perte de données)'
    )
    parser.add_argument(
        '--check',
        action='store_true',
        help='Vérifie simplement la connexion à la base de données'
    )
    
    args = parser.parse_args()
    
    if args.check:
        try:
            from app import app, db
            with app.app_context():
                db.engine.connect()
            logger.info("Connexion à la base de données réussie!")
            return 0
        except Exception as e:
            logger.error(f"Erreur de connexion : {e}")
            return 1
    
    try:
        if args.drop:
            response = input("ATTENTION: Toutes les données seront perdues. Continuer ? (oui/non) : ")
            if response.lower() != 'oui':
                logger.info("Opération annulée.")
                return 0
        
        success = init_database(drop_existing=args.drop)
        if success:
            logger.info("\nInitialisation terminée avec succès!")
        return 0 if success else 1
        
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation : {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
