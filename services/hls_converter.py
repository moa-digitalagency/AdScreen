import subprocess
import os
import signal
import tempfile
import logging
import threading
import time
import shutil
import fcntl
from pathlib import Path

logger = logging.getLogger(__name__)

class HLSConverter:
    HLS_TEMP_DIR = Path(tempfile.gettempdir()) / 'adscreen_hls'
    
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
    def _get_pid_file(cls, screen_code):
        return cls.get_output_dir(screen_code) / 'ffmpeg.pid'

    @classmethod
    def _get_url_file(cls, screen_code):
        return cls.get_output_dir(screen_code) / 'source.url'

    @classmethod
    def _get_lock_file(cls, screen_code):
        return cls.get_output_dir(screen_code) / 'process.lock'
    
    @classmethod
    def get_current_url(cls, screen_code):
        try:
            url_file = cls._get_url_file(screen_code)
            if url_file.exists():
                return url_file.read_text().strip()
        except Exception:
            pass
        return None
    
    @classmethod
    def is_running(cls, screen_code):
        pid_file = cls._get_pid_file(screen_code)
        if not pid_file.exists():
            return False

        try:
            pid = int(pid_file.read_text().strip())
            os.kill(pid, 0)
            return True
        except (ValueError, ProcessLookupError, OSError):
            return False
    
    @staticmethod
    def stop_existing_process(screen_code):
        """Arrête et tue complètement le processus FFmpeg + nettoie les fichiers"""
        
        lock_fd = None
        try:
            output_dir = HLSConverter.get_output_dir(screen_code)
            output_dir.mkdir(parents=True, exist_ok=True)

            lock_path = HLSConverter._get_lock_file(screen_code)
            lock_fd = open(lock_path, 'w')
            fcntl.flock(lock_fd, fcntl.LOCK_EX)

            if HLSConverter.is_running(screen_code):
                try:
                    pid_file = HLSConverter._get_pid_file(screen_code)
                    pid = int(pid_file.read_text().strip())

                    logger.info(f'[{screen_code}] Killing FFmpeg process (PID: {pid})')
                    
                    try:
                        os.kill(pid, signal.SIGTERM)
                        for _ in range(20):
                            time.sleep(0.1)
                            os.kill(pid, 0)
                    except OSError:
                        pass
                    except Exception:
                         try:
                             os.kill(pid, signal.SIGKILL)
                         except OSError:
                             pass
                    
                    logger.info(f'[{screen_code}] Process killed')
                
                except Exception as e:
                    logger.error(f'[{screen_code}] Error killing process: {e}')
            
            if output_dir.exists():
                try:
                    logger.info(f'[{screen_code}] Cleaning up files in {output_dir}')
                    for item in output_dir.iterdir():
                        if item.name != 'process.lock':
                            if item.is_dir():
                                shutil.rmtree(item)
                            else:
                                item.unlink()
                except Exception as e:
                    logger.error(f'[{screen_code}] Error cleaning files: {e}')

        except Exception as e:
            logger.error(f'[{screen_code}] Error in stop_existing_process: {e}')
        finally:
            if lock_fd:
                try:
                    fcntl.flock(lock_fd, fcntl.LOCK_UN)
                    lock_fd.close()
                except Exception:
                    pass
    
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
        
        lock_path = HLSConverter._get_lock_file(screen_code)
        lock_fd = open(lock_path, 'w')
        
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_EX)

            if HLSConverter.is_running(screen_code):
                current_url = HLSConverter.get_current_url(screen_code)
                if current_url == source_url:
                    logger.info(f'[{screen_code}] Stream already running for this URL')
                    manifest_path = HLSConverter.get_manifest_path(screen_code)
                    if manifest_path.exists():
                        return str(manifest_path)

                logger.info(f'[{screen_code}] Stopping existing stream before starting new one')
                pid_file = HLSConverter._get_pid_file(screen_code)
                if pid_file.exists():
                    try:
                        pid = int(pid_file.read_text().strip())
                        os.kill(pid, signal.SIGKILL)
                    except:
                        pass

                for item in output_dir.iterdir():
                    if item.name != 'process.lock':
                        try:
                            if item.is_dir():
                                shutil.rmtree(item)
                            else:
                                item.unlink()
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

            logger.info(f'[{screen_code}] Starting FFmpeg conversion')
            logger.info(f'[{screen_code}] Source: {source_url[:60]}...')
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid
            )
            
            HLSConverter._get_pid_file(screen_code).write_text(str(process.pid))
            HLSConverter._get_url_file(screen_code).write_text(source_url)
            
            logger.info(f'[{screen_code}] FFmpeg PID: {process.pid}')
            
            def monitor_process():
                try:
                    stdout, stderr = process.communicate()
                    if process.returncode != 0 and process.returncode != -15 and process.returncode != -9:
                        stderr_text = stderr.decode('utf-8', errors='ignore')[:500]
                        logger.error(f'[{screen_code}] FFmpeg error (code {process.returncode}): {stderr_text}')
                except Exception as e:
                    logger.error(f'[{screen_code}] Process monitoring error: {e}')
            
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

                    process.kill()
                    try:
                        HLSConverter._get_pid_file(screen_code).unlink()
                    except:
                        pass

                    raise Exception(f'Manifest creation timeout after {elapsed:.1f}s')
                
                logger.info(f'[{screen_code}] Conversion ready in {time.time() - start_time:.1f}s')
            
            return str(manifest_path)

        except Exception as e:
            logger.error(f'[{screen_code}] Conversion error: {e}')
            raise
        finally:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
            lock_fd.close()
    
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
