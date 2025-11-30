import subprocess
import json
import os


def get_video_info(file_path):
    """
    Get video information using ffprobe.
    
    Args:
        file_path: Path to the video file
    
    Returns:
        dict: Video info with width, height, duration, or None on error
    """
    try:
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            file_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            return None
        
        data = json.loads(result.stdout)
        
        video_stream = None
        for stream in data.get('streams', []):
            if stream.get('codec_type') == 'video':
                video_stream = stream
                break
        
        if not video_stream:
            return None
        
        width = video_stream.get('width')
        height = video_stream.get('height')
        
        duration = None
        if 'duration' in video_stream:
            duration = float(video_stream['duration'])
        elif 'format' in data and 'duration' in data['format']:
            duration = float(data['format']['duration'])
        
        fps = None
        fps_str = str(video_stream.get('r_frame_rate', ''))
        if '/' in fps_str:
            try:
                num, den = fps_str.split('/')
                fps = float(num) / float(den) if float(den) != 0 else None
            except (ValueError, ZeroDivisionError):
                fps = None
        
        return {
            'width': width,
            'height': height,
            'duration': duration,
            'codec': video_stream.get('codec_name'),
            'fps': fps
        }
        
    except Exception as e:
        return None


def get_video_duration(file_path):
    """
    Get the duration of a video file in seconds.
    
    Args:
        file_path: Path to the video file
    
    Returns:
        float: Duration in seconds or None on error
    """
    info = get_video_info(file_path)
    if info:
        return info.get('duration')
    return None


def validate_video(file_path, target_width, target_height, max_duration):
    """
    Validate a video file against screen resolution and duration requirements.
    
    Args:
        file_path: Path to the video file
        target_width: Expected width (screen resolution)
        target_height: Expected height (screen resolution)
        max_duration: Maximum allowed duration in seconds
    
    Returns:
        tuple: (is_valid, width, height, duration, error_message)
    """
    info = get_video_info(file_path)
    
    if not info:
        return False, None, None, None, "Impossible de lire les informations de la vidéo"
    
    width = info.get('width')
    height = info.get('height')
    duration = info.get('duration')
    
    if not width or not height:
        return False, None, None, duration, "Impossible de déterminer la résolution de la vidéo"
    
    if duration is None:
        return False, width, height, None, "Impossible de déterminer la durée de la vidéo"
    
    if duration > max_duration + 1:
        return False, width, height, duration, f"La vidéo est trop longue ({duration:.1f}s). Maximum autorisé: {max_duration}s"
    
    return True, width, height, duration, None


def extract_thumbnail(video_path, output_path, timestamp=1):
    """
    Extract a thumbnail from a video file.
    
    Args:
        video_path: Path to the video file
        output_path: Path for the output thumbnail
        timestamp: Timestamp in seconds to extract the frame
    
    Returns:
        bool: True on success, False on error
    """
    try:
        cmd = [
            'ffmpeg',
            '-y',
            '-i', video_path,
            '-ss', str(timestamp),
            '-vframes', '1',
            '-q:v', '2',
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, timeout=30)
        return result.returncode == 0 and os.path.exists(output_path)
        
    except Exception:
        return False
