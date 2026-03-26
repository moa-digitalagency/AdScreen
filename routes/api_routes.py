"""
 * Nom de l'application : Shabaka AdScreen
 * Description : API routes for dashboard and screen management
 * Produit de : MOA Digital Agency, www.myoneart.com
 * Fait par : Aisance KALONJI, www.aisancekalonji.com
 * Auditer par : La CyberConfiance, www.cyberconfiance.com
"""
from flask import Blueprint, jsonify, request, send_file, make_response
from flask_login import login_required, current_user
from app import db
from models import Screen, Content, Booking, StatLog
from datetime import datetime, timedelta
from sqlalchemy import func
import io

api_bp = Blueprint('api', __name__)


@api_bp.route('/cities/<country_code>')
def get_cities_by_country(country_code):
    from utils.currencies import get_cities_for_country
    cities = get_cities_for_country(country_code)
    return jsonify({
        'country': country_code,
        'cities': cities
    })


@api_bp.route('/screens/status')
@login_required
def screens_status():
    if current_user.is_superadmin():
        screens = Screen.query.all()
    else:
        screens = Screen.query.filter_by(organization_id=current_user.organization_id).all()
    
    now = datetime.utcnow()
    threshold = timedelta(minutes=2)
    
    result = []
    for screen in screens:
        is_online = screen.last_heartbeat and (now - screen.last_heartbeat) < threshold
        
        result.append({
            'id': screen.id,
            'name': screen.name,
            'status': screen.status if is_online else 'offline',
            'last_heartbeat': screen.last_heartbeat.isoformat() if screen.last_heartbeat else None,
            'is_active': screen.is_active
        })
    
    return jsonify(result)


@api_bp.route('/screen/<int:screen_id>/stats')
@login_required
def screen_stats(screen_id):
    if current_user.is_superadmin():
        screen = Screen.query.get_or_404(screen_id)
    else:
        screen = Screen.query.filter_by(
            id=screen_id,
            organization_id=current_user.organization_id
        ).first_or_404()
    
    today = datetime.utcnow().date()
    week_ago = today - timedelta(days=7)
    
    daily_plays = db.session.query(
        func.date(StatLog.played_at).label('date'),
        func.count(StatLog.id).label('count')
    ).filter(
        StatLog.screen_id == screen_id,
        StatLog.played_at >= week_ago
    ).group_by(func.date(StatLog.played_at)).all()
    
    category_stats = db.session.query(
        StatLog.content_category,
        func.count(StatLog.id).label('count')
    ).filter(
        StatLog.screen_id == screen_id,
        StatLog.played_at >= week_ago
    ).group_by(StatLog.content_category).all()
    
    return jsonify({
        'daily_plays': [{'date': str(d.date), 'count': d.count} for d in daily_plays],
        'category_stats': [{'category': c.content_category, 'count': c.count} for c in category_stats]
    })


@api_bp.route('/dashboard/summary')
@login_required
def dashboard_summary():
    if current_user.is_superadmin():
        total_screens = Screen.query.count()
        online_screens = Screen.query.filter(
            Screen.status.in_(['online', 'playing'])
        ).count()
        pending_contents = Content.query.filter_by(status='pending').count()
        total_revenue = db.session.query(func.sum(Booking.total_price)).filter(
            Booking.payment_status == 'paid'
        ).scalar() or 0
    else:
        org_id = current_user.organization_id
        total_screens = Screen.query.filter_by(organization_id=org_id).count()
        online_screens = Screen.query.filter(
            Screen.organization_id == org_id,
            Screen.status.in_(['online', 'playing'])
        ).count()
        pending_contents = Content.query.join(Screen).filter(
            Screen.organization_id == org_id,
            Content.status == 'pending'
        ).count()
        total_revenue = db.session.query(func.sum(Booking.total_price)).join(Screen).filter(
            Screen.organization_id == org_id,
            Booking.payment_status == 'paid'
        ).scalar() or 0
    
    return jsonify({
        'total_screens': total_screens,
        'online_screens': online_screens,
        'pending_contents': pending_contents,
        'total_revenue': float(total_revenue)
    })


@api_bp.route('/documents/cgv-pdf')
def download_cgv_pdf():
    """Generate and serve CGV (Terms & Conditions) PDF"""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
        from io import BytesIO

        # Create PDF in memory
        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#059669'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )

        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#047857'),
            spaceAfter=12,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        )

        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['BodyText'],
            fontSize=10,
            alignment=TA_JUSTIFY,
            spaceAfter=12,
            leading=14
        )

        # Title
        story.append(Paragraph("Conditions Générales de Vente", title_style))
        story.append(Spacer(1, 0.3*inch))

        # Content sections
        sections = [
            ("1. Objet", "Les présentes conditions générales régissent l'utilisation de la plateforme Shabaka AdScreen pour la location d'espaces publicitaires numériques."),
            ("2. Services", "Shabaka AdScreen propose la mise à disposition d'écrans publicitaires numériques permettant aux annonceurs de diffuser du contenu publicitaire pendant une période définie."),
            ("3. Tarification", "Les tarifs sont communiqués lors de la création d'une réservation. Le paiement doit être effectué avant la diffusion du contenu. Les prix affichés incluent la TVA applicable."),
            ("4. Réservation", "Les réservations sont confirmées après paiement complet. Les modifications ou annulations doivent être effectuées au moins 48 heures avant la date de diffusion programmée."),
            ("5. Contenu", "L'annonceur est responsable du contenu diffusé. Shabaka AdScreen se réserve le droit de refuser ou de retirer tout contenu jugé inapproprié, illégal ou contraire à ses conditions."),
            ("6. Propriété Intellectuelle", "L'annonceur garantit posséder tous les droits sur le contenu fourni. Shabaka AdScreen n'est pas responsable de tout manquement à la propriété intellectuelle."),
            ("7. Garanties", "Shabaka AdScreen garantit le fonctionnement des écrans selon les spécifications convenues. En cas de dysfonctionnement, une compensation proportionnelle pourra être accordée."),
            ("8. Limitation de Responsabilité", "Shabaka AdScreen n'est pas responsable des pertes indirectes ou des dommages consécutifs. La responsabilité est limitée au montant de la réservation."),
            ("9. Données Personnelles", "Les données collectées sont traitées conformément à la réglementation RGPD. Consultez notre politique de confidentialité pour plus d'informations."),
            ("10. Droit Applicable", "Ces conditions sont régies par la loi française. Tout litige sera résolu devant les tribunaux compétents.")
        ]

        for title, content in sections:
            story.append(Paragraph(title, heading_style))
            story.append(Paragraph(content, body_style))
            story.append(Spacer(1, 0.1*inch))

        # Footer
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph(
            "© 2026 Shabaka AdScreen - Tous droits réservés",
            ParagraphStyle(
                'Footer',
                parent=styles['Normal'],
                fontSize=8,
                textColor=colors.grey,
                alignment=TA_CENTER
            )
        ))

        # Build PDF
        doc.build(story)
        pdf_buffer.seek(0)

        # Serve PDF
        response = make_response(send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='CGV-Shabaka-AdScreen.pdf'
        ))
        response.headers['Content-Disposition'] = 'attachment; filename="CGV-Shabaka-AdScreen.pdf"'
        return response

    except Exception as e:
        return jsonify({'error': f'Erreur lors de la génération du PDF: {str(e)}'}), 500
