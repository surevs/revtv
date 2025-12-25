# -*- coding: utf-8 -*-
"""
JioTV Service Module for RevTV
Production implementation with actual JioTV API endpoints.

API Reference (unofficial, reverse-engineered):
- Auth: api.jio.com, auth.media.jio.com
- Channels: jiotv.data.cdn.jio.com
- Playback: jiotvapi.media.jio.com

Copyright (c) 2025 surevs - MIT License
"""
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import requests
import json
import time
import hashlib
import base64
from urllib.parse import urlencode

ADDON = xbmcaddon.Addon()

# API Endpoints (based on JioTV Go and community research)
API_ENDPOINTS = {
    'send_otp': 'https://api.jio.com/v3/dip/user/otp/send',
    'verify_otp': 'https://api.jio.com/v3/dip/user/otp/verify',
    'refresh_token': 'https://auth.media.jio.com/tokenservice/apis/v1/refreshtoken',
    'channels': 'https://jiotv.data.cdn.jio.com/apis/v3.0/getMobileChannelList/get/',
    'epg': 'https://jiotv.data.cdn.jio.com/apis/v1.3/getepg/get/',
    'playback': 'https://jiotvapi.media.jio.com/playback/apis/v1.1/geturl',
}

# Headers mimicking JioTV Android app
BASE_HEADERS = {
    'User-Agent': 'JioTV-Android/1.0.4',
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'x-platform': 'android',
    'x-platform-version': '10',
    'x-app-version': '1.0.4',
}

# Category mappings
CATEGORIES = {
    'Entertainment': 5, 'Movies': 6, 'Kids': 7, 'Sports': 8,
    'Lifestyle': 9, 'Infotainment': 10, 'News': 12, 'Music': 13,
    'Devotional': 14, 'Business': 15, 'Educational': 16, 'Shopping': 17,
}

# Language mappings
LANGUAGES = {
    'Hindi': 1, 'Marathi': 2, 'Punjabi': 3, 'Urdu': 4, 'Bengali': 5,
    'English': 6, 'Malayalam': 7, 'Tamil': 8, 'Gujarati': 9, 'Odia': 10,
    'Telugu': 11, 'Bhojpuri': 12, 'Kannada': 13, 'Assamese': 14, 'Nepali': 15,
}

LANG_NAMES = {v: k for k, v in LANGUAGES.items()}
CAT_NAMES = {v: k for k, v in CATEGORIES.items()}


class JioTVAPI:
    """JioTV API Client with OTP authentication."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(BASE_HEADERS)
        self._load_credentials()
    
    def _load_credentials(self):
        """Load stored credentials from addon settings."""
        self.access_token = ADDON.getSetting('jiotv_token') or ''
        self.refresh_token = ADDON.getSetting('jiotv_refresh_token') or ''
        self.subscriber_id = ADDON.getSetting('jiotv_subscriber_id') or ''
        self.device_id = ADDON.getSetting('jiotv_device_id') or self._generate_device_id()
    
    def _generate_device_id(self):
        """Generate a unique device ID."""
        import uuid
        device_id = str(uuid.uuid4())
        ADDON.setSetting('jiotv_device_id', device_id)
        return device_id
    
    def _save_credentials(self, data):
        """Save authentication tokens to addon settings."""
        if 'authToken' in data:
            ADDON.setSetting('jiotv_token', data['authToken'])
            self.access_token = data['authToken']
        if 'refreshToken' in data:
            ADDON.setSetting('jiotv_refresh_token', data['refreshToken'])
            self.refresh_token = data['refreshToken']
        if 'subscriberId' in data:
            ADDON.setSetting('jiotv_subscriber_id', data['subscriberId'])
            self.subscriber_id = data['subscriberId']
    
    def is_logged_in(self):
        """Check if user has valid credentials."""
        return bool(self.access_token)
    
    def get_auth_headers(self):
        """Get headers with authentication token."""
        headers = BASE_HEADERS.copy()
        if self.access_token:
            headers['Authorization'] = f'Bearer {self.access_token}'
            headers['subscriberId'] = self.subscriber_id
            headers['deviceId'] = self.device_id
        return headers
    
    def send_otp(self, mobile_number):
        """Send OTP to mobile number."""
        try:
            payload = {
                'number': f'+91{mobile_number}',
                'otp_type': 'login'
            }
            resp = self.session.post(
                API_ENDPOINTS['send_otp'],
                json=payload,
                timeout=30
            )
            log(f"Send OTP response: {resp.status_code}")
            return resp.status_code == 200
        except Exception as e:
            log(f"Send OTP error: {e}", xbmc.LOGERROR)
            return False
    
    def verify_otp(self, mobile_number, otp):
        """Verify OTP and get authentication tokens."""
        try:
            payload = {
                'number': f'+91{mobile_number}',
                'otp': otp,
                'deviceInfo': {
                    'consumptionDeviceName': 'Kodi RevTV',
                    'info': {
                        'type': 'android',
                        'platform': {'name': 'android'},
                        'androidId': self.device_id
                    }
                }
            }
            resp = self.session.post(
                API_ENDPOINTS['verify_otp'],
                json=payload,
                timeout=30
            )
            log(f"Verify OTP response: {resp.status_code}")
            
            if resp.status_code == 200:
                data = resp.json()
                self._save_credentials(data)
                return True
            return False
        except Exception as e:
            log(f"Verify OTP error: {e}", xbmc.LOGERROR)
            return False
    
    def refresh_auth_token(self):
        """Refresh authentication token."""
        if not self.refresh_token:
            return False
        try:
            headers = self.get_auth_headers()
            payload = {'refreshToken': self.refresh_token}
            resp = self.session.post(
                API_ENDPOINTS['refresh_token'],
                headers=headers,
                json=payload,
                timeout=30
            )
            if resp.status_code == 200:
                data = resp.json()
                self._save_credentials(data)
                return True
            return False
        except Exception as e:
            log(f"Refresh token error: {e}", xbmc.LOGERROR)
            return False
    
    def get_channels(self, language_id=None, category_id=None):
        """Fetch all channels, optionally filtered."""
        try:
            resp = self.session.get(
                API_ENDPOINTS['channels'],
                headers=self.get_auth_headers(),
                timeout=30
            )
            if resp.status_code != 200:
                log(f"Get channels failed: {resp.status_code}")
                return []
            
            data = resp.json()
            channels = data.get('result', [])
            
            # Filter by language
            if language_id:
                channels = [c for c in channels if c.get('channelLanguageId') == language_id]
            
            # Filter by category
            if category_id:
                channels = [c for c in channels if c.get('channelCategoryId') == category_id]
            
            log(f"Got {len(channels)} channels")
            return channels
        except Exception as e:
            log(f"Get channels error: {e}", xbmc.LOGERROR)
            return []
    
    def get_playback_url(self, channel_id):
        """Get stream URL for a channel."""
        if not self.is_logged_in():
            return None
        
        try:
            headers = self.get_auth_headers()
            headers['channel_id'] = str(channel_id)
            headers['stream_type'] = 'Seek'
            
            # Quality setting
            quality = ADDON.getSetting('jiotv_quality') or 'auto'
            quality_map = {'low': 'low', 'medium': 'medium', 'high': 'high', 'auto': 'high'}
            headers['quality'] = quality_map.get(quality, 'high')
            
            resp = self.session.get(
                f"{API_ENDPOINTS['playback']}?channel_id={channel_id}",
                headers=headers,
                timeout=30
            )
            
            if resp.status_code == 200:
                data = resp.json()
                return data.get('result', {}).get('url')
            elif resp.status_code == 401:
                # Token expired, try refresh
                if self.refresh_auth_token():
                    return self.get_playback_url(channel_id)
            
            log(f"Get playback URL failed: {resp.status_code}")
            return None
        except Exception as e:
            log(f"Get playback URL error: {e}", xbmc.LOGERROR)
            return None


# Global API instance
api = JioTVAPI()


def log(message, level=xbmc.LOGINFO):
    """Log message to Kodi log."""
    xbmc.log(f"[RevTV:JioTV] {message}", level)


def show_menu(handle, get_url):
    """Show JioTV main menu."""
    xbmcplugin.setPluginCategory(handle, 'JioTV')
    xbmcplugin.setContent(handle, 'files')
    
    items = []
    
    if not api.is_logged_in():
        items.append(('🔐 Login with OTP', get_url(action='jiotv_login'), False))
    else:
        items.extend([
            ('📺 Telugu Channels', get_url(action='jiotv_channels', language=11), True),
            ('🎬 Entertainment', get_url(action='jiotv_channels', category=5), True),
            ('🎥 Movies', get_url(action='jiotv_channels', category=6), True),
            ('📰 News', get_url(action='jiotv_channels', category=12), True),
            ('⚽ Sports', get_url(action='jiotv_channels', category=8), True),
            ('📂 All Categories', get_url(action='jiotv_categories'), True),
            ('🌐 All Languages', get_url(action='jiotv_languages'), True),
            ('📋 All Channels', get_url(action='jiotv_channels'), True),
            ('🚪 Logout', get_url(action='jiotv_logout'), False),
        ])
    
    for label, url, is_folder in items:
        li = xbmcgui.ListItem(label=label)
        xbmcplugin.addDirectoryItem(handle, url, li, isFolder=is_folder)
    
    xbmcplugin.endOfDirectory(handle)


def show_categories(handle, get_url):
    """Show all channel categories."""
    xbmcplugin.setPluginCategory(handle, 'Categories')
    for name, cat_id in sorted(CATEGORIES.items()):
        li = xbmcgui.ListItem(label=name)
        url = get_url(action='jiotv_channels', category=cat_id)
        xbmcplugin.addDirectoryItem(handle, url, li, isFolder=True)
    xbmcplugin.endOfDirectory(handle)


def show_languages(handle, get_url):
    """Show all languages."""
    xbmcplugin.setPluginCategory(handle, 'Languages')
    for name, lang_id in sorted(LANGUAGES.items()):
        li = xbmcgui.ListItem(label=name)
        url = get_url(action='jiotv_channels', language=lang_id)
        xbmcplugin.addDirectoryItem(handle, url, li, isFolder=True)
    xbmcplugin.endOfDirectory(handle)


def show_channels(handle, get_url, category=None, language=None):
    """Show channels list."""
    xbmcplugin.setPluginCategory(handle, 'Channels')
    xbmcplugin.setContent(handle, 'videos')
    
    # Convert string params to int
    cat_id = int(category) if category else None
    lang_id = int(language) if language else None
    
    channels = api.get_channels(language_id=lang_id, category_id=cat_id)
    
    if not channels:
        xbmcgui.Dialog().notification('RevTV', 'No channels found or login required')
    
    for ch in channels:
        channel_id = ch.get('channel_id')
        channel_name = ch.get('channel_name', 'Unknown')
        logo_url = ch.get('logoUrl', '')
        
        # Build logo URL
        if logo_url and not logo_url.startswith('http'):
            logo_url = f"https://jiotv.catchup.cdn.jio.com/dare_images/images/{logo_url}"
        
        # Create list item
        li = xbmcgui.ListItem(label=channel_name)
        li.setArt({
            'thumb': logo_url,
            'icon': logo_url,
            'fanart': logo_url
        })
        
        # Add info
        lang_name = LANG_NAMES.get(ch.get('channelLanguageId', 0), 'Unknown')
        cat_name = CAT_NAMES.get(ch.get('channelCategoryId', 0), 'Unknown')
        li.setInfo('video', {
            'title': channel_name,
            'genre': cat_name,
            'plotoutline': f"{lang_name} | {cat_name}",
            'mediatype': 'video'
        })
        li.setProperty('IsPlayable', 'true')
        
        url = get_url(action='jiotv_play', channel_id=channel_id)
        xbmcplugin.addDirectoryItem(handle, url, li, isFolder=False)
    
    xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.endOfDirectory(handle)


def play_channel(handle, channel_id):
    """Play a channel."""
    if not api.is_logged_in():
        xbmcgui.Dialog().ok('RevTV', 'Please login first')
        return
    
    stream_url = api.get_playback_url(channel_id)
    
    if not stream_url:
        xbmcgui.Dialog().ok('RevTV', 'Failed to get stream URL. Please try again.')
        return
    
    # Create playable item with adaptive streaming
    li = xbmcgui.ListItem(path=stream_url)
    
    # Enable InputStream Adaptive for HLS
    if ADDON.getSettingBool('adaptive_enabled'):
        li.setProperty('inputstream', 'inputstream.adaptive')
        li.setProperty('inputstream.adaptive.manifest_type', 'hls')
        
        # Quality-based bandwidth limits for low bandwidth optimization
        quality = ADDON.getSetting('jiotv_quality') or 'auto'
        if quality == 'low':
            li.setProperty('inputstream.adaptive.max_bandwidth', '500000')
        elif quality == 'medium':
            li.setProperty('inputstream.adaptive.max_bandwidth', '1500000')
        elif quality == 'high':
            li.setProperty('inputstream.adaptive.max_bandwidth', '5000000')
        # auto = no limit
    
    li.setMimeType('application/vnd.apple.mpegurl')
    li.setContentLookup(False)
    
    xbmcplugin.setResolvedUrl(handle, True, li)
    log(f"Playing channel {channel_id}")


def login():
    """Login with mobile number and OTP."""
    dialog = xbmcgui.Dialog()
    
    # Get mobile number
    mobile = dialog.input('Enter Jio Mobile Number (10 digits)', type=xbmcgui.INPUT_NUMERIC)
    if not mobile or len(mobile) != 10:
        dialog.ok('RevTV', 'Please enter a valid 10-digit Jio mobile number')
        return False
    
    # Send OTP
    dialog.notification('RevTV', 'Sending OTP...', time=2000)
    if not api.send_otp(mobile):
        dialog.ok('RevTV', 'Failed to send OTP. Please check your number and try again.')
        return False
    
    # Get OTP
    otp = dialog.input('Enter OTP received on your phone', type=xbmcgui.INPUT_NUMERIC)
    if not otp:
        return False
    
    # Verify OTP
    dialog.notification('RevTV', 'Verifying...', time=2000)
    if api.verify_otp(mobile, otp):
        ADDON.setSetting('jiotv_mobile', mobile)
        dialog.ok('RevTV', 'Login successful! You can now watch JioTV channels.')
        xbmc.executebuiltin('Container.Refresh')
        return True
    else:
        dialog.ok('RevTV', 'Invalid OTP. Please try again.')
        return False


def logout():
    """Clear stored credentials."""
    ADDON.setSetting('jiotv_token', '')
    ADDON.setSetting('jiotv_refresh_token', '')
    ADDON.setSetting('jiotv_subscriber_id', '')
    ADDON.setSetting('jiotv_mobile', '')
    api._load_credentials()
    xbmcgui.Dialog().ok('RevTV', 'Logged out successfully')
    xbmc.executebuiltin('Container.Refresh')
