# pyright: reportArgumentType=false, reportReturnType=false
"""
Service de gestion IPTV - Parsing M3U et gestion des chaines
"""
import re
import logging
import urllib.request
import urllib.error
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class IPTVChannel:
    """Representation d'une chaine IPTV"""
    name: str
    url: str
    logo: Optional[str] = None
    group: Optional[str] = None
    tvg_id: Optional[str] = None
    tvg_name: Optional[str] = None


def parse_m3u_content(content: str) -> List[IPTVChannel]:
    """
    Parse le contenu d'un fichier M3U et extrait les chaines.
    
    Args:
        content: Contenu du fichier M3U
        
    Returns:
        Liste de chaines IPTVChannel
    """
    channels = []
    lines = content.strip().split('\n')
    
    if not lines or not lines[0].startswith('#EXTM3U'):
        logger.warning("Format M3U invalide: header manquant")
        return channels
    
    current_info = None
    
    for line in lines[1:]:
        line = line.strip()
        
        if not line:
            continue
            
        if line.startswith('#EXTINF:'):
            current_info = parse_extinf_line(line)
        elif not line.startswith('#') and current_info:
            channel = IPTVChannel(
                name=current_info.get('name', 'Sans nom'),
                url=line,
                logo=current_info.get('logo'),
                group=current_info.get('group'),
                tvg_id=current_info.get('tvg_id'),
                tvg_name=current_info.get('tvg_name')
            )
            channels.append(channel)
            current_info = None
        elif not line.startswith('#'):
            channel = IPTVChannel(name='Sans nom', url=line)
            channels.append(channel)
    
    logger.info(f"Parsed {len(channels)} channels from M3U")
    return channels


def parse_extinf_line(line: str) -> Dict[str, Optional[str]]:
    """
    Parse une ligne EXTINF pour extraire les metadonnees.
    
    Format: #EXTINF:-1 tvg-id="id" tvg-name="name" tvg-logo="logo" group-title="group",Channel Name
    """
    info = {
        'name': None,
        'logo': None,
        'group': None,
        'tvg_id': None,
        'tvg_name': None
    }
    
    tvg_id_match = re.search(r'tvg-id="([^"]*)"', line)
    if tvg_id_match:
        info['tvg_id'] = tvg_id_match.group(1)
    
    tvg_name_match = re.search(r'tvg-name="([^"]*)"', line)
    if tvg_name_match:
        info['tvg_name'] = tvg_name_match.group(1)
    
    logo_match = re.search(r'tvg-logo="([^"]*)"', line)
    if logo_match:
        info['logo'] = logo_match.group(1)
    
    group_match = re.search(r'group-title="([^"]*)"', line)
    if group_match:
        info['group'] = group_match.group(1)
    
    name_match = re.search(r',(.+)$', line)
    if name_match:
        info['name'] = name_match.group(1).strip()
    elif info['tvg_name']:
        info['name'] = info['tvg_name']
    
    return info


def fetch_m3u_from_url(url: str, timeout: int = 30) -> Optional[str]:
    """
    Telecharge le contenu M3U depuis une URL.
    
    Args:
        url: URL du fichier M3U
        timeout: Timeout en secondes
        
    Returns:
        Contenu du fichier M3U ou None en cas d'erreur
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        request = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(request, timeout=timeout) as response:
            content = response.read()
            try:
                return content.decode('utf-8')
            except UnicodeDecodeError:
                return content.decode('latin-1')
                
    except urllib.error.URLError as e:
        logger.error(f"Erreur URL M3U: {e}")
        return None
    except Exception as e:
        logger.error(f"Erreur telechargement M3U: {e}")
        return None


def get_channels_from_organization(organization, limit: Optional[int] = None) -> List[IPTVChannel]:
    """
    Recupere la liste des chaines IPTV d'une organisation.
    
    Args:
        organization: Instance Organization avec iptv_m3u_url
        limit: Nombre maximum de chaines a retourner (None = toutes)
        
    Returns:
        Liste de chaines IPTVChannel
    """
    if not organization.has_iptv or not organization.iptv_m3u_url:
        return []
    
    content = fetch_m3u_from_url(organization.iptv_m3u_url)
    if not content:
        return []
    
    channels = parse_m3u_content(content)
    
    if limit and len(channels) > limit:
        return channels[:limit]
    
    return channels


def get_total_channel_count(organization) -> int:
    """
    Recupere le nombre total de chaines sans les charger toutes.
    
    Args:
        organization: Instance Organization avec iptv_m3u_url
        
    Returns:
        Nombre de chaines
    """
    if not organization.has_iptv or not organization.iptv_m3u_url:
        return 0
    
    content = fetch_m3u_from_url(organization.iptv_m3u_url)
    if not content:
        return 0
    
    count = content.count('#EXTINF:')
    return count


def get_channels_grouped(channels: List[IPTVChannel]) -> Dict[str, List[IPTVChannel]]:
    """
    Groupe les chaines par categorie.
    
    Args:
        channels: Liste de chaines
        
    Returns:
        Dictionnaire groupe -> liste de chaines
    """
    grouped = {}
    
    for channel in channels:
        group = channel.group or 'Autres'
        if group not in grouped:
            grouped[group] = []
        grouped[group].append(channel)
    
    sorted_groups = dict(sorted(grouped.items()))
    
    return sorted_groups


def validate_m3u_url(url: str) -> Dict[str, Any]:
    """
    Valide une URL M3U et retourne des infos.
    
    Args:
        url: URL a valider
        
    Returns:
        Dict avec 'valid', 'channel_count', 'error'
    """
    if not url:
        return {'valid': False, 'channel_count': 0, 'error': 'URL vide'}
    
    if not url.startswith(('http://', 'https://')):
        return {'valid': False, 'channel_count': 0, 'error': 'URL invalide'}
    
    content = fetch_m3u_from_url(url, timeout=15)
    if not content:
        return {'valid': False, 'channel_count': 0, 'error': 'Impossible de telecharger le fichier'}
    
    channels = parse_m3u_content(content)
    if not channels:
        return {'valid': False, 'channel_count': 0, 'error': 'Aucune chaine trouvee dans le fichier'}
    
    return {'valid': True, 'channel_count': len(channels), 'error': None}
