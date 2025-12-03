import subprocess
import os
import signal
import tempfile
import logging
import threading
import time
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)

class HLSConverter:
    HLS_TEMP_DIR = Path(tempfile.gettempdir()) / 'adscreen_hls'
    RUNNING_PROCESSES = {}
    _current_urls = {}
    _lock = threading.Lock()
    
    def __init__(self):
        self.HLS_TEMP_DIR.mkdir(parents=True, exist_ok=True)
    
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
    def get_current_url(cls, screen_code):
        with cls._lock:
            return cls._current_urls.get(screen_code)
    
    @classmethod
    def is_running(cls, screen_code):
        with cls._lock:
            if screen_code in cls.RUNNING_PROCESSES:
                proc = cls.RUNNING_PROCESSES[screen_code]
                if proc.poll() is None:
                    return True
                else:
                    del cls.RUNNING_PROCESSES[screen_code]
        return False
    
    @staticmethod
    def stop_existing_process(screen_code):
        """Arrête et tue complètement le processus FFmpeg + nettoie les fichiers"""
        
        with HLSConverter._lock:
            if screen_code in HLSConverter.RUNNING_PROCESSES:
                process = HLSConverter.RUNNING_PROCESSES[screen_code]
                
                try:
                    logger.info(f'[{screen_code}] Killing FFmpeg process (PID: {process.pid})')
                    
                    process.terminate()
                    try:
                        process.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        logger.warning(f'[{screen_code}] Force killing process')
                        process.kill()
                        try:
                            process.wait(timeout=2)
                        except:
                            pass
                    
                    logger.info(f'[{screen_code}] Process killed')
                
                except Exception as e:
                    logger.error(f'[{screen_code}] Error killing process: {e}')
                
                del HLSConverter.RUNNING_PROCESSES[screen_code]
            
            if screen_code in HLSConverter._current_urls:
                del HLSConverter._current_urls[screen_code]
        
        output_dir = HLSConverter.HLS_TEMP_DIR / screen_code
        if output_dir.exists():
            try:
                logger.info(f'[{screen_code}] Cleaning up files in {output_dir}')
                shutil.rmtree(output_dir)
                output_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logger.error(f'[{screen_code}] Error cleaning files: {e}')
    
    @classmethod
    def stop_stream(cls, screen_code):
        """Alias pour stop_existing_process"""
        cls.stop_existing_process(screen_code)
    
    @classmethod
    def cleanup_screen(cls, screen_code):
        """Alias pour stop_existing_process"""
        cls.stop_existing_process(screen_code)
    
    @staticmethod
    def convert_mpegts_to_hls_file(source_url, screen_code, wait_for_manifest=True):
        """
        Convertit MPEG-TS en HLS
        wait_for_manifest: Attend que le manifeste soit prêt avant de retourner
        """
        HLSConverter.init()
        
        output_dir = HLSConverter.HLS_TEMP_DIR / screen_code
        output_dir.mkdir(parents=True, exist_ok=True)
        
        manifest_path = output_dir / 'stream.m3u8'
        segment_pattern = str(output_dir / 'segment%03d.ts')
        
        cmd = [
            'ffmpeg',
            '-y',
            '-hide_banner',
            '-loglevel', 'warning',
            '-reconnect', '1',
            '-reconnect_streamed', '1',
            '-reconnect_delay_max', '5',
            '-fflags', '+genpts+discardcorrupt',
            '-user_agent', 'VLC/3.0.18 LibVLC/3.0.18',
            '-i', source_url,
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-b:a', '96k',
            '-f', 'hls',
            '-hls_time', '2',
            '-hls_list_size', '3',
            '-hls_flags', 'delete_segments+independent_segments',
            '-hls_segment_filename', segment_pattern,
            str(manifest_path)
        ]
        
        try:
            logger.info(f'[{screen_code}] Starting FFmpeg conversion')
            logger.info(f'[{screen_code}] Source: {source_url[:60]}...')
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid
            )
            
            with HLSConverter._lock:
                HLSConverter.RUNNING_PROCESSES[screen_code] = process
                HLSConverter._current_urls[screen_code] = source_url
            
            logger.info(f'[{screen_code}] FFmpeg PID: {process.pid}')
            
            def monitor_process():
                try:
                    stdout, stderr = process.communicate(timeout=3600)
                    if process.returncode != 0 and process.returncode != -15 and process.returncode != -9:
                        stderr_text = stderr.decode('utf-8', errors='ignore')[:500]
                        logger.error(f'[{screen_code}] FFmpeg error (code {process.returncode}): {stderr_text}')
                except subprocess.TimeoutExpired:
                    pass
                except Exception as e:
                    logger.error(f'[{screen_code}] Process error: {e}')
                finally:
                    with HLSConverter._lock:
                        if screen_code in HLSConverter.RUNNING_PROCESSES:
                            if HLSConverter.RUNNING_PROCESSES[screen_code] == process:
                                del HLSConverter.RUNNING_PROCESSES[screen_code]
                        if screen_code in HLSConverter._current_urls:
                            del HLSConverter._current_urls[screen_code]
                    logger.info(f'[{screen_code}] Process ended')
            
            thread = threading.Thread(target=monitor_process, daemon=True)
            thread.start()
            
            if wait_for_manifest:
                logger.info(f'[{screen_code}] Waiting for manifest...')
                
                max_wait = 15
                start_time = time.time()
                manifest_ready = False
                
                while time.time() - start_time < max_wait:
                    if manifest_path.exists():
                        try:
                            with open(manifest_path, 'r') as f:
                                content = f.read()
                            
                            if '.ts' in content and '#EXTINF' in content:
                                logger.info(f'[{screen_code}] Manifest ready with segments')
                                manifest_ready = True
                                break
                        except:
                            pass
                    
                    time.sleep(0.2)
                
                if not manifest_ready:
                    elapsed = time.time() - start_time
                    logger.error(f'[{screen_code}] Manifest not ready after {elapsed:.1f}s')
                    HLSConverter.stop_existing_process(screen_code)
                    raise Exception(f'Manifest creation timeout after {elapsed:.1f}s')
                
                logger.info(f'[{screen_code}] Conversion ready in {time.time() - start_time:.1f}s')
            
            return str(manifest_path)
        
        except Exception as e:
            logger.error(f'[{screen_code}] Conversion error: {e}')
            HLSConverter.stop_existing_process(screen_code)
            raise
    
    @classmethod
    def start_conversion(cls, source_url, screen_code):
        """Démarre une nouvelle conversion (appelle convert_mpegts_to_hls_file)"""
        return cls.convert_mpegts_to_hls_file(source_url, screen_code, wait_for_manifest=True)
    
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
