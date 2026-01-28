"""
 * Nom de l'application : Shabaka AdScreen
 * Description : Entry point for development server
 * Produit de : MOA Digital Agency, www.myoneart.com
 * Fait par : Aisance KALONJI, www.aisancekalonji.com
 * Auditer par : La CyberConfiance, www.cyberconfiance.com
"""
from gevent import monkey
monkey.patch_all()

from app import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
