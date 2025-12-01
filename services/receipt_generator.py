from PIL import Image, ImageDraw, ImageFont
import io
import os
import base64
from datetime import datetime


CURRENCIES = [
    {"code": "EUR", "name": "Euro", "symbol": "€", "country": "EU", "flag": "🇪🇺"},
    {"code": "USD", "name": "Dollar américain", "symbol": "$", "country": "US", "flag": "🇺🇸"},
    {"code": "GBP", "name": "Livre sterling", "symbol": "£", "country": "GB", "flag": "🇬🇧"},
    {"code": "CHF", "name": "Franc suisse", "symbol": "CHF", "country": "CH", "flag": "🇨🇭"},
    {"code": "CAD", "name": "Dollar canadien", "symbol": "C$", "country": "CA", "flag": "🇨🇦"},
    {"code": "AUD", "name": "Dollar australien", "symbol": "A$", "country": "AU", "flag": "🇦🇺"},
    {"code": "JPY", "name": "Yen japonais", "symbol": "¥", "country": "JP", "flag": "🇯🇵"},
    {"code": "CNY", "name": "Yuan chinois", "symbol": "¥", "country": "CN", "flag": "🇨🇳"},
    {"code": "INR", "name": "Roupie indienne", "symbol": "₹", "country": "IN", "flag": "🇮🇳"},
    {"code": "BRL", "name": "Real brésilien", "symbol": "R$", "country": "BR", "flag": "🇧🇷"},
    {"code": "MXN", "name": "Peso mexicain", "symbol": "$", "country": "MX", "flag": "🇲🇽"},
    {"code": "ARS", "name": "Peso argentin", "symbol": "$", "country": "AR", "flag": "🇦🇷"},
    {"code": "COP", "name": "Peso colombien", "symbol": "$", "country": "CO", "flag": "🇨🇴"},
    {"code": "CLP", "name": "Peso chilien", "symbol": "$", "country": "CL", "flag": "🇨🇱"},
    {"code": "PEN", "name": "Sol péruvien", "symbol": "S/", "country": "PE", "flag": "🇵🇪"},
    {"code": "MAD", "name": "Dirham marocain", "symbol": "DH", "country": "MA", "flag": "🇲🇦"},
    {"code": "TND", "name": "Dinar tunisien", "symbol": "DT", "country": "TN", "flag": "🇹🇳"},
    {"code": "DZD", "name": "Dinar algérien", "symbol": "DA", "country": "DZ", "flag": "🇩🇿"},
    {"code": "EGP", "name": "Livre égyptienne", "symbol": "E£", "country": "EG", "flag": "🇪🇬"},
    {"code": "SAR", "name": "Riyal saoudien", "symbol": "SR", "country": "SA", "flag": "🇸🇦"},
    {"code": "AED", "name": "Dirham des EAU", "symbol": "AED", "country": "AE", "flag": "🇦🇪"},
    {"code": "QAR", "name": "Riyal qatari", "symbol": "QR", "country": "QA", "flag": "🇶🇦"},
    {"code": "KWD", "name": "Dinar koweïtien", "symbol": "KD", "country": "KW", "flag": "🇰🇼"},
    {"code": "BHD", "name": "Dinar bahreïni", "symbol": "BD", "country": "BH", "flag": "🇧🇭"},
    {"code": "OMR", "name": "Rial omanais", "symbol": "OMR", "country": "OM", "flag": "🇴🇲"},
    {"code": "JOD", "name": "Dinar jordanien", "symbol": "JD", "country": "JO", "flag": "🇯🇴"},
    {"code": "LBP", "name": "Livre libanaise", "symbol": "L£", "country": "LB", "flag": "🇱🇧"},
    {"code": "ILS", "name": "Shekel israélien", "symbol": "₪", "country": "IL", "flag": "🇮🇱"},
    {"code": "TRY", "name": "Livre turque", "symbol": "₺", "country": "TR", "flag": "🇹🇷"},
    {"code": "RUB", "name": "Rouble russe", "symbol": "₽", "country": "RU", "flag": "🇷🇺"},
    {"code": "UAH", "name": "Hryvnia ukrainienne", "symbol": "₴", "country": "UA", "flag": "🇺🇦"},
    {"code": "PLN", "name": "Zloty polonais", "symbol": "zł", "country": "PL", "flag": "🇵🇱"},
    {"code": "CZK", "name": "Couronne tchèque", "symbol": "Kč", "country": "CZ", "flag": "🇨🇿"},
    {"code": "HUF", "name": "Forint hongrois", "symbol": "Ft", "country": "HU", "flag": "🇭🇺"},
    {"code": "RON", "name": "Leu roumain", "symbol": "lei", "country": "RO", "flag": "🇷🇴"},
    {"code": "BGN", "name": "Lev bulgare", "symbol": "лв", "country": "BG", "flag": "🇧🇬"},
    {"code": "HRK", "name": "Kuna croate", "symbol": "kn", "country": "HR", "flag": "🇭🇷"},
    {"code": "RSD", "name": "Dinar serbe", "symbol": "din", "country": "RS", "flag": "🇷🇸"},
    {"code": "SEK", "name": "Couronne suédoise", "symbol": "kr", "country": "SE", "flag": "🇸🇪"},
    {"code": "NOK", "name": "Couronne norvégienne", "symbol": "kr", "country": "NO", "flag": "🇳🇴"},
    {"code": "DKK", "name": "Couronne danoise", "symbol": "kr", "country": "DK", "flag": "🇩🇰"},
    {"code": "ISK", "name": "Couronne islandaise", "symbol": "kr", "country": "IS", "flag": "🇮🇸"},
    {"code": "ZAR", "name": "Rand sud-africain", "symbol": "R", "country": "ZA", "flag": "🇿🇦"},
    {"code": "NGN", "name": "Naira nigérian", "symbol": "₦", "country": "NG", "flag": "🇳🇬"},
    {"code": "KES", "name": "Shilling kényan", "symbol": "KSh", "country": "KE", "flag": "🇰🇪"},
    {"code": "GHS", "name": "Cedi ghanéen", "symbol": "₵", "country": "GH", "flag": "🇬🇭"},
    {"code": "XOF", "name": "Franc CFA (UEMOA)", "symbol": "CFA", "country": "SN", "flag": "🇸🇳"},
    {"code": "XAF", "name": "Franc CFA (CEMAC)", "symbol": "FCFA", "country": "CM", "flag": "🇨🇲"},
    {"code": "MUR", "name": "Roupie mauricienne", "symbol": "Rs", "country": "MU", "flag": "🇲🇺"},
    {"code": "TZS", "name": "Shilling tanzanien", "symbol": "TSh", "country": "TZ", "flag": "🇹🇿"},
    {"code": "UGX", "name": "Shilling ougandais", "symbol": "USh", "country": "UG", "flag": "🇺🇬"},
    {"code": "RWF", "name": "Franc rwandais", "symbol": "FRw", "country": "RW", "flag": "🇷🇼"},
    {"code": "ETB", "name": "Birr éthiopien", "symbol": "Br", "country": "ET", "flag": "🇪🇹"},
    {"code": "THB", "name": "Baht thaïlandais", "symbol": "฿", "country": "TH", "flag": "🇹🇭"},
    {"code": "VND", "name": "Dong vietnamien", "symbol": "₫", "country": "VN", "flag": "🇻🇳"},
    {"code": "IDR", "name": "Roupie indonésienne", "symbol": "Rp", "country": "ID", "flag": "🇮🇩"},
    {"code": "MYR", "name": "Ringgit malaisien", "symbol": "RM", "country": "MY", "flag": "🇲🇾"},
    {"code": "SGD", "name": "Dollar singapourien", "symbol": "S$", "country": "SG", "flag": "🇸🇬"},
    {"code": "PHP", "name": "Peso philippin", "symbol": "₱", "country": "PH", "flag": "🇵🇭"},
    {"code": "KRW", "name": "Won sud-coréen", "symbol": "₩", "country": "KR", "flag": "🇰🇷"},
    {"code": "TWD", "name": "Dollar taïwanais", "symbol": "NT$", "country": "TW", "flag": "🇹🇼"},
    {"code": "HKD", "name": "Dollar de Hong Kong", "symbol": "HK$", "country": "HK", "flag": "🇭🇰"},
    {"code": "NZD", "name": "Dollar néo-zélandais", "symbol": "NZ$", "country": "NZ", "flag": "🇳🇿"},
    {"code": "PKR", "name": "Roupie pakistanaise", "symbol": "Rs", "country": "PK", "flag": "🇵🇰"},
    {"code": "BDT", "name": "Taka bangladais", "symbol": "৳", "country": "BD", "flag": "🇧🇩"},
    {"code": "LKR", "name": "Roupie srilankaise", "symbol": "Rs", "country": "LK", "flag": "🇱🇰"},
    {"code": "NPR", "name": "Roupie népalaise", "symbol": "Rs", "country": "NP", "flag": "🇳🇵"},
    {"code": "MMK", "name": "Kyat birman", "symbol": "K", "country": "MM", "flag": "🇲🇲"},
    {"code": "KHR", "name": "Riel cambodgien", "symbol": "៛", "country": "KH", "flag": "🇰🇭"},
    {"code": "LAK", "name": "Kip laotien", "symbol": "₭", "country": "LA", "flag": "🇱🇦"},
]


def get_currency_by_code(code):
    for currency in CURRENCIES:
        if currency["code"] == code:
            return currency
    return {"code": code, "name": code, "symbol": code, "country": "", "flag": ""}


def get_currency_symbol(code):
    currency = get_currency_by_code(code)
    return currency.get("symbol", code)


def generate_receipt_image(booking, screen, content, qr_base64=None):
    width = 400
    height = 600
    
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    try:
        font_bold = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
        font_regular = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
    except:
        font_bold = ImageFont.load_default()
        font_regular = ImageFont.load_default()
        font_small = ImageFont.load_default()
        font_large = ImageFont.load_default()
    
    draw.rectangle([0, 0, width, 70], fill='#10b981')
    
    draw.text((width//2, 25), "SHABAKA ADSCREEN", fill='white', font=font_large, anchor='mm')
    draw.text((width//2, 50), "Reçu de Réservation", fill='#d1fae5', font=font_regular, anchor='mm')
    
    y = 90
    
    draw.rectangle([30, y, width-30, y+50], fill='#f3f4f6', outline='#e5e7eb')
    draw.text((width//2, y+15), "N° Réservation", fill='#6b7280', font=font_small, anchor='mm')
    draw.text((width//2, y+35), booking.reservation_number or "---", fill='#111827', font=font_bold, anchor='mm')
    
    y += 70
    
    currency = get_currency_by_code(screen.organization.currency if hasattr(screen.organization, 'currency') and screen.organization.currency else 'EUR')
    currency_symbol = currency.get('symbol', '€')
    
    details = [
        ("Écran", screen.name[:25]),
        ("Établissement", screen.organization.name[:25]),
        ("Type", content.content_type.capitalize()),
        ("Durée créneau", f"{booking.slot_duration}s"),
        ("Diffusions", str(booking.num_plays)),
        ("Date début", booking.start_date.strftime('%d/%m/%Y') if booking.start_date else "-"),
        ("Prix unitaire", f"{booking.price_per_play:.2f} {currency_symbol}"),
    ]
    
    if booking.end_date:
        details.insert(6, ("Date fin", booking.end_date.strftime('%d/%m/%Y')))
    
    for label, value in details:
        draw.text((40, y), label, fill='#6b7280', font=font_regular)
        draw.text((width-40, y), value, fill='#111827', font=font_regular, anchor='ra')
        y += 22
    
    y += 10
    draw.line([(30, y), (width-30, y)], fill='#e5e7eb', width=1)
    y += 15
    
    draw.rectangle([30, y, width-30, y+40], fill='#10b981', outline='#059669')
    draw.text((width//2, y+20), f"TOTAL: {booking.total_price:.2f} {currency_symbol}", fill='white', font=font_large, anchor='mm')
    
    y += 60
    
    draw.rectangle([30, y, width-30, y+35], fill='#fef3c7', outline='#fcd34d')
    draw.text((width//2, y+17), "En attente de validation", fill='#92400e', font=font_regular, anchor='mm')
    
    y += 55
    
    if qr_base64:
        try:
            qr_data = base64.b64decode(qr_base64)
            qr_img = Image.open(io.BytesIO(qr_data))
            qr_size = 80
            qr_img = qr_img.resize((qr_size, qr_size))
            qr_x = (width - qr_size) // 2
            img.paste(qr_img, (qr_x, y))
            y += qr_size + 10
        except Exception as e:
            pass
    
    footer_y = height - 40
    draw.text((width//2, footer_y), screen.organization.name, fill='#6b7280', font=font_small, anchor='mm')
    draw.text((width//2, footer_y + 15), datetime.now().strftime('%d/%m/%Y %H:%M'), fill='#9ca3af', font=font_small, anchor='mm')
    
    return img


def save_receipt_image(booking, screen, content, qr_base64=None):
    img = generate_receipt_image(booking, screen, content, qr_base64)
    
    receipts_dir = os.path.join('static', 'uploads', 'receipts')
    os.makedirs(receipts_dir, exist_ok=True)
    
    filename = f"receipt_{booking.reservation_number}.png"
    filepath = os.path.join(receipts_dir, filename)
    
    img.save(filepath, 'PNG')
    
    return filepath


def get_receipt_base64(booking, screen, content, qr_base64=None):
    img = generate_receipt_image(booking, screen, content, qr_base64)
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    return base64.b64encode(buffer.getvalue()).decode('utf-8')
