from PIL import Image
import os


def validate_image(file_path, target_width, target_height, tolerance=1):
    """
    Validate an image file.
    
    Args:
        file_path: Path to the image file
        target_width: Expected width (screen resolution) - not enforced, content adapts
        target_height: Expected height (screen resolution) - not enforced, content adapts
        tolerance: Pixel tolerance for ratio comparison
    
    Returns:
        tuple: (is_valid, width, height, error_message)
    """
    try:
        with Image.open(file_path) as img:
            width, height = img.size
            return True, width, height, None
            
    except Exception as e:
        return False, None, None, f"Erreur lors de la lecture de l'image: {str(e)}"


def get_image_dimensions(file_path):
    """
    Get the dimensions of an image file.
    
    Args:
        file_path: Path to the image file
    
    Returns:
        tuple: (width, height) or (None, None) on error
    """
    try:
        with Image.open(file_path) as img:
            return img.size
    except Exception:
        return None, None


def resize_image(file_path, target_width, target_height, output_path=None):
    """
    Resize an image to fit the target dimensions while maintaining aspect ratio.
    
    Args:
        file_path: Path to the source image
        target_width: Target width
        target_height: Target height
        output_path: Path for the resized image (optional, overwrites source if not provided)
    
    Returns:
        str: Path to the resized image or None on error
    """
    try:
        with Image.open(file_path) as img:
            img_ratio = img.width / img.height
            target_ratio = target_width / target_height
            
            if img_ratio > target_ratio:
                new_width = target_width
                new_height = int(target_width / img_ratio)
            else:
                new_height = target_height
                new_width = int(target_height * img_ratio)
            
            resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            final = Image.new('RGB', (target_width, target_height), (0, 0, 0))
            x_offset = (target_width - new_width) // 2
            y_offset = (target_height - new_height) // 2
            
            if resized.mode == 'RGBA':
                final.paste(resized, (x_offset, y_offset), resized)
            else:
                final.paste(resized, (x_offset, y_offset))
            
            save_path = output_path or file_path
            final.save(save_path, quality=90)
            
            return save_path
            
    except Exception as e:
        return None
