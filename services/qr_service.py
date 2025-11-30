import qrcode
import io
import base64
from flask import url_for


def generate_qr_code(data, box_size=10, border=4):
    """
    Generate a QR code image.
    
    Args:
        data: The data to encode in the QR code
        box_size: Size of each box in the QR code
        border: Border size around the QR code
    
    Returns:
        bytes: PNG image data
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    return buffer.getvalue()


def generate_qr_base64(data, box_size=10, border=4):
    """
    Generate a QR code as a base64-encoded string.
    
    Args:
        data: The data to encode in the QR code
        box_size: Size of each box in the QR code
        border: Border size around the QR code
    
    Returns:
        str: Base64-encoded PNG image
    """
    img_data = generate_qr_code(data, box_size, border)
    return base64.b64encode(img_data).decode()


def generate_screen_booking_url(screen, external=True):
    """
    Generate the booking URL for a screen.
    
    Args:
        screen: Screen model instance
        external: Whether to generate an external URL
    
    Returns:
        str: The booking URL
    """
    return url_for('booking.screen_booking', screen_code=screen.unique_code, _external=external)
