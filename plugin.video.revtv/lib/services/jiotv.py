# -*- coding: utf-8 -*-
"""
JioTV Service Module for RevTV
Handles authentication, channel listing, and streaming for JioTV.
"""
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import requests
import json
import time
from lib.auth.token_manager import TokenManager
from lib.utils.api_client import APIClient

ADDON = xbmcaddon.Addon()
API_BASE = "https://jiotvapi.media.jio.com/playback/apis/v1"
AUTH_BASE = "https://jiotvapi.media.jio.com/authapi/apis/v1"

CATEGORIES = {
    'Entertainment': 5, 'Movies': 6, 'Kids': 7, 'Sports': 8,
    'Lifestyle': 9, 'Infotainment': 10, 'News': 12, 'Music': 13,
    'Devotional': 14, 'Business': 15, 'Educational': 16, 'Shopping': 17,
    'JioDarshan': 18
}

LANGUAGES = {
    'Hindi': 1, 'Marathi': 2, 'Punjabi': 3, 'Urdu': 4, 'Bengali': 5,
    'English': 6, 'Malayalam': 7, 'Tamil': 8, 'Gujarati': 9, 'Odia': 10,
    'Telugu': 11, 'Bhojpuri': 12, 'Kannada': 13, 'Assamese': 14,
    'Nepali': 15, 'French': 16
}

token_mgr = TokenManager('jiotv')
client = APIClient()


def is_logged_in():
    """Check if user is logged in."""
    return bool(ADDON.getSetting('jiotv_token'))


def show_menu(handle, get_url):
    """Show JioTV main menu."""
    xbmcplugin.setPluginCategory(handle, 'JioTV')
    
    if not is_logged_in():
        item = xbmcgui.ListItem(label='[B]Login with OTP[/B]')
        xbmcplugin.addDirectoryItem(handle, get_url(action='jiotv_login'), item, isFolder=False)
    else:
        items = [
            ('Live TV by Category', 'jiotv_categories'),
            ('Telugu Channels', 'jiotv_channels', {'language': 'Telugu'}),
            ('All Channels', 'jiotv_channels', {}),
        ]
        for item_data in items:
            label, action = item_data[0], item_data[1]
            params = item_data[2] if len(item_data) > 2 else {}
            li = xbmcgui.ListItem(label=label)
            xbmcplugin.addDirectoryItem(handle, get_url(action=action, **params), li, isFolder=True)
    
    xbmcplugin.endOfDirectory(handle)


def show_categories(handle, get_url):
    """Show channel categories."""
    xbmcplugin.setPluginCategory(handle, 'Categories')
    for name, cat_id in CATEGORIES.items():
        li = xbmcgui.ListItem(label=name)
        xbmcplugin.addDirectoryItem(handle, get_url(action='jiotv_channels', category=cat_id), li, isFolder=True)
    xbmcplugin.endOfDirectory(handle)


def show_channels(handle, get_url, category=None, language=None):
    """Show channels list."""
    xbmcplugin.setPluginCategory(handle, 'Channels')
    xbmcplugin.setContent(handle, 'videos')
    
    channels = get_channels()
    if category:
        channels = [c for c in channels if c.get('channelCategoryId') == int(category)]
    if language:
        lang_id = LANGUAGES.get(language, 11)  # Default Telugu
        channels = [c for c in channels if c.get('channelLanguageId') == lang_id]
    
    for ch in channels:
        li = xbmcgui.ListItem(label=ch.get('channel_name', 'Unknown'))
        li.setArt({'thumb': ch.get('logoUrl', ''), 'icon': ch.get('logoUrl', '')})
        li.setInfo('video', {'title': ch.get('channel_name'), 'mediatype': 'video'})
        li.setProperty('IsPlayable', 'true')
        url = get_url(action='jiotv_play', channel_id=ch.get('channel_id'))
        xbmcplugin.addDirectoryItem(handle, url, li, isFolder=False)
    
    xbmcplugin.endOfDirectory(handle)


def get_channels():
    """Fetch channel list from API."""
    try:
        headers = get_headers()
        resp = client.get(f"{API_BASE}/channels", headers=headers)
        return resp.json().get('result', []) if resp.ok else []
    except Exception as e:
        xbmc.log(f"[RevTV] Error fetching channels: {e}", xbmc.LOGERROR)
        return []


def get_headers():
    """Get API headers with auth token."""
    return {
        'User-Agent': 'JioTV/1.0',
        'Authorization': f"Bearer {ADDON.getSetting('jiotv_token')}",
        'Content-Type': 'application/json'
    }


def login():
    """Login with mobile number and OTP."""
    dialog = xbmcgui.Dialog()
    mobile = dialog.input('Enter Jio Mobile Number', type=xbmcgui.INPUT_NUMERIC)
    if not mobile or len(mobile) != 10:
        dialog.ok('Error', 'Please enter valid 10-digit mobile number')
        return False
    
    # Request OTP
    try:
        resp = client.post(f"{AUTH_BASE}/sendotp", json={'number': f'+91{mobile}'})
        if not resp.ok:
            dialog.ok('Error', 'Failed to send OTP')
            return False
    except Exception as e:
        dialog.ok('Error', f'Network error: {e}')
        return False
    
    # Enter OTP
    otp = dialog.input('Enter OTP received on your phone', type=xbmcgui.INPUT_NUMERIC)
    if not otp:
        return False
    
    # Verify OTP
    try:
        resp = client.post(f"{AUTH_BASE}/verifyotp", json={'number': f'+91{mobile}', 'otp': otp})
        if resp.ok:
            data = resp.json()
            ADDON.setSetting('jiotv_mobile', mobile)
            ADDON.setSetting('jiotv_token', data.get('authToken', ''))
            ADDON.setSetting('jiotv_refresh_token', data.get('refreshToken', ''))
            dialog.ok('Success', 'Login successful!')
            return True
        else:
            dialog.ok('Error', 'Invalid OTP')
            return False
    except Exception as e:
        dialog.ok('Error', f'Verification failed: {e}')
        return False


def play_channel(handle, channel_id):
    """Play a channel stream."""
    if not is_logged_in():
        xbmcgui.Dialog().ok('Error', 'Please login first')
        return
    
    quality = ADDON.getSetting('jiotv_quality') or 'auto'
    
    try:
        headers = get_headers()
        resp = client.get(f"{API_BASE}/playbackurl/{channel_id}", headers=headers)
        if resp.ok:
            data = resp.json()
            stream_url = data.get('result', {}).get('url', '')
            
            if stream_url:
                li = xbmcgui.ListItem(path=stream_url)
                # Enable adaptive streaming for quality optimization
                if ADDON.getSettingBool('adaptive_enabled'):
                    li.setProperty('inputstream', 'inputstream.adaptive')
                    li.setProperty('inputstream.adaptive.manifest_type', 'hls')
                    # Low bandwidth optimization
                    if quality == 'low':
                        li.setProperty('inputstream.adaptive.max_bandwidth', '500000')
                    elif quality == 'medium':
                        li.setProperty('inputstream.adaptive.max_bandwidth', '1500000')
                    elif quality == 'high':
                        li.setProperty('inputstream.adaptive.max_bandwidth', '5000000')
                    # Auto = no limit, adaptive chooses
                
                xbmcplugin.setResolvedUrl(handle, True, li)
            else:
                xbmcgui.Dialog().ok('Error', 'Stream URL not found')
        else:
            xbmcgui.Dialog().ok('Error', 'Failed to get stream')
    except Exception as e:
        xbmc.log(f"[RevTV] Playback error: {e}", xbmc.LOGERROR)
        xbmcgui.Dialog().ok('Error', f'Playback failed: {e}')
