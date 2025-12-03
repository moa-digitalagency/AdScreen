import subprocess
import os
import tempfile
import logging
import threading
import shutil
import time
from pathlib import Path

logger = logging.getLogger(__name__)

class HLSConverter:
    HLS_TEMP_DIR = Path(tempfile.gettempdir()) / 'adscreen_hls'
    _processes = {}
    _current_urls = {}
    _lock = threading.Lock()
    
    @classmethod
    def init(cls):
        cls.HLS_TEMP_DIR.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_output_dir(cls, screen_code):
        return cls.HLS_TEMP_DIR / screen_code
    
    @classmethod
    def get_manifest_path(cls, screen_code):
        return cls.get_output_dir(screen_code) / 'stream.m3u8'
    
    @classmethod
    def is_running(cls, screen_code):
        with cls._lock:
            if screen_code in cls._processes:
                proc = cls._processes[screen_code]
                if proc.poll() is None:
                    return True
                else:
                    del cls._processes[screen_code]
        return False
    
    @classmethod
    def cleanup_screen(cls, screen_code):
        with cls._lock:
            if screen_code in cls._processes:
                proc = cls._processes[screen_code]
                try:
                    proc.terminate()
                    proc.wait(timeout=5)
                except:
                    try:
                        proc.kill()
                    except:
                        pass
                del cls._processes[screen_code]
            if screen_code in cls._current_urls:
                del cls._current_urls[screen_code]
        
        output_dir = cls.get_output_dir(screen_code)
        if output_dir.exists():
            try:
                shutil.rmtree(output_dir)
                logger.info(f'[{screen_code}] Cleaned up HLS directory')
            except Exception as e:
                logger.warning(f'[{screen_code}] Cleanup error: {e}')
    
    @classmethod
    def stop_stream(cls, screen_code):
        logger.info(f'[{screen_code}] Stopping stream...')
        with cls._lock:
            if screen_code in cls._processes:
                proc = cls._processes[screen_code]
                try:
                    logger.info(f'[{screen_code}] Terminating FFmpeg process (PID: {proc.pid})')
                    proc.terminate()
                    try:
                        proc.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        logger.warning(f'[{screen_code}] Force killing FFmpeg process')
                        proc.kill()
                        proc.wait()
                    logger.info(f'[{screen_code}] FFmpeg process stopped')
                except Exception as e:
                    logger.error(f'[{screen_code}] Error stopping process: {e}')
                del cls._processes[screen_code]
            if screen_code in cls._current_urls:
                del cls._current_urls[screen_code]
        
        output_dir = cls.get_output_dir(screen_code)
        if output_dir.exists():
            for f in output_dir.glob('*.ts'):
                try:
                    f.unlink()
                except:
                    pass
            for f in output_dir.glob('*.m3u8'):
                try:
                    f.unlink()
                except:
                    pass
            logger.info(f'[{screen_code}] Cleaned up HLS segments')
    
    @classmethod
    def get_current_url(cls, screen_code):
        with cls._lock:
            return cls._current_urls.get(screen_code)
    
    @classmethod
    def start_conversion(cls, source_url, screen_code):
        cls.init()
        
        current_url = cls.get_current_url(screen_code)
        if current_url and current_url != source_url:
            logger.info(f'[{screen_code}] Channel changed, stopping previous stream')
            logger.info(f'[{screen_code}] Old URL: {current_url[:60]}...')
            logger.info(f'[{screen_code}] New URL: {source_url[:60]}...')
            cls.stop_stream(screen_code)
        
        if cls.is_running(screen_code):
            manifest_path = cls.get_manifest_path(screen_code)
            if manifest_path.exists():
                logger.info(f'[{screen_code}] FFmpeg already running with same channel, using existing manifest')
                return str(manifest_path)
        
        output_dir = cls.get_output_dir(screen_code)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for f in output_dir.glob('*.ts'):
            try:
                f.unlink()
            except:
                pass
        for f in output_dir.glob('*.m3u8'):
            try:
                f.unlink()
            except:
                pass
        
        manifest_path = output_dir / 'stream.m3u8'
        segment_pattern = str(output_dir / 'segment%03d.ts')
        
        cmd = [
            'ffmpeg',
            '-y',
            '-hide_banner',
            '-loglevel', 'warning',
            '-reconnect', '1',
            '-reconnect_streamed', '1',
            '-reconnect_delay_max', '10',
            '-fflags', '+genpts+discardcorrupt',
            '-user_agent', 'VLC/3.0.18 LibVLC/3.0.18',
            '-i', source_url,
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-b:a', '128k',
            '-f', 'hls',
            '-hls_time', '4',
            '-hls_list_size', '10',
            '-hls_flags', 'independent_segments+append_list',
            '-hls_segment_filename', segment_pattern,
            str(manifest_path)
        ]
        
        try:
            logger.info(f'[{screen_code}] Starting FFmpeg conversion')
            logger.info(f'[{screen_code}] Output dir: {output_dir}')
            logger.info(f'[{screen_code}] Source: {source_url[:60]}...')
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            with cls._lock:
                if screen_code in cls._processes:
                    try:
                        cls._processes[screen_code].terminate()
                    except:
                        pass
                cls._processes[screen_code] = process
                cls._current_urls[screen_code] = source_url
            
            def monitor_process():
                stdout, stderr = process.communicate()
                if process.returncode != 0 and process.returncode != -15:
                    stderr_text = stderr.decode('utf-8', errors='ignore')[:500]
                    logger.error(f'[{screen_code}] FFmpeg error (code {process.returncode}): {stderr_text}')
                else:
                    logger.info(f'[{screen_code}] FFmpeg process ended normally')
                with cls._lock:
                    if screen_code in cls._processes and cls._processes[screen_code] == process:
                        del cls._processes[screen_code]
                    if screen_code in cls._current_urls:
                        del cls._current_urls[screen_code]
            
            thread = threading.Thread(target=monitor_process, daemon=True)
            thread.start()
            
            for i in range(100):
                if manifest_path.exists() and manifest_path.stat().st_size > 0:
                    segments = list(output_dir.glob('segment*.ts'))
                    if segments:
                        logger.info(f'[{screen_code}] Manifest created with {len(segments)} segment(s) after {i*0.1:.1f}s')
                        return str(manifest_path)
                time.sleep(0.1)
            
            if manifest_path.exists():
                logger.info(f'[{screen_code}] Manifest exists (no segments yet)')
                return str(manifest_path)
            
            logger.error(f'[{screen_code}] Manifest not created after 10s')
            raise Exception('Manifest creation timeout')
        
        except Exception as e:
            logger.error(f'[{screen_code}] Conversion error: {e}')
            raise
    
    @classmethod
    def get_fresh_manifest(cls, screen_code):
        manifest_path = cls.get_manifest_path(screen_code)
        if not manifest_path.exists():
            return None
        try:
            with open(manifest_path, 'r') as f:
                return f.read()
        except:
            return None
    
    @classmethod
    def get_segment_path(cls, screen_code, segment_name):
        segment_path = cls.get_output_dir(screen_code) / segment_name
        return segment_path if segment_path.exists() else None
    
    @classmethod
    def rewrite_manifest(cls, manifest_content, screen_code):
        import re
        rewritten = re.sub(
            r'(segment\d+\.ts)',
            f'/player/tv-segment/{screen_code}/\\1',
            manifest_content
        )
        return rewritten
    
    @classmethod
    def list_available_segments(cls, screen_code):
        output_dir = cls.get_output_dir(screen_code)
        if not output_dir.exists():
            return []
        return [f.name for f in sorted(output_dir.glob('segment*.ts'))]
