# -*- coding: utf-8 -*-
"""
RevTV - Indian Regional TV Streaming for Kodi

Copyright (c) 2025 surevs (revanth.mvs@hotmail.com)
Licensed under MIT License - See LICENSE file

DISCLAIMER: This addon requires valid subscriptions to access content.
Users must provide their own credentials. Not affiliated with any streaming service.
"""

import sys
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon

from urllib.parse import urlencode, parse_qsl

# Addon info
ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')
ADDON_NAME = ADDON.getAddonInfo('name')
ADDON_VERSION = ADDON.getAddonInfo('version')
ADDON_PATH = ADDON.getAddonInfo('path')
ADDON_ICON = ADDON.getAddonInfo('icon')

# Plugin handle
HANDLE = int(sys.argv[1])

# Import services
try:
    from lib.services import jiotv, hotstar, sonyliv, zee5, etvwin, sunnxt, aha
    from lib.auth import token_manager
    from lib.utils import api_client
except ImportError as e:
    xbmc.log(f"[RevTV] Import error: {e}", xbmc.LOGERROR)


def get_url(**kwargs):
    """Create a plugin URL with the given parameters."""
    return f"{sys.argv[0]}?{urlencode(kwargs)}"


def log(message, level=xbmc.LOGINFO):
    """Log a message to Kodi log."""
    xbmc.log(f"[{ADDON_NAME}] {message}", level)


def show_notification(message, heading=ADDON_NAME, icon=ADDON_ICON, time=5000):
    """Show a Kodi notification."""
    xbmcgui.Dialog().notification(heading, message, icon, time)


def show_main_menu():
    """Display the main menu with available services."""
    log("Showing main menu")
    
    services = [
        {'name': 'JioTV', 'action': 'jiotv', 'icon': 'jiotv.png', 'enabled': True},
        {'name': 'JioHotstar', 'action': 'hotstar', 'icon': 'hotstar.png', 'enabled': False},
        {'name': 'SonyLIV', 'action': 'sonyliv', 'icon': 'sonyliv.png', 'enabled': False},
        {'name': 'Zee5', 'action': 'zee5', 'icon': 'zee5.png', 'enabled': False},
        {'name': 'ETV Win', 'action': 'etvwin', 'icon': 'etvwin.png', 'enabled': False},
        {'name': 'Sun NXT', 'action': 'sunnxt', 'icon': 'sunnxt.png', 'enabled': False},
        {'name': 'Aha', 'action': 'aha', 'icon': 'aha.png', 'enabled': False},
    ]
    
    xbmcplugin.setPluginCategory(HANDLE, ADDON_NAME)
    xbmcplugin.setContent(HANDLE, 'videos')
    
    for service in services:
        if service['enabled']:
            label = service['name']
        else:
            label = f"{service['name']} [Coming Soon]"
        
        list_item = xbmcgui.ListItem(label=label)
        list_item.setArt({'icon': ADDON_ICON, 'fanart': ADDON_ICON})
        list_item.setInfo('video', {'title': label, 'mediatype': 'video'})
        
        url = get_url(action=service['action']) if service['enabled'] else get_url(action='coming_soon')
        
        xbmcplugin.addDirectoryItem(HANDLE, url, list_item, isFolder=True)
    
    # Settings menu item
    settings_item = xbmcgui.ListItem(label='[B]Settings[/B]')
    settings_item.setArt({'icon': ADDON_ICON})
    xbmcplugin.addDirectoryItem(HANDLE, get_url(action='settings'), settings_item, isFolder=True)
    
    xbmcplugin.endOfDirectory(HANDLE)


def show_coming_soon():
    """Show coming soon message."""
    show_notification("This service is coming soon!", time=3000)


def open_settings():
    """Open addon settings."""
    ADDON.openSettings()


def router(params):
    """Route to the appropriate action based on parameters."""
    action = params.get('action')
    
    if action is None:
        show_main_menu()
    elif action == 'jiotv':
        jiotv.show_menu(HANDLE, get_url)
    elif action == 'jiotv_categories':
        jiotv.show_categories(HANDLE, get_url)
    elif action == 'jiotv_channels':
        category = params.get('category')
        jiotv.show_channels(HANDLE, get_url, category)
    elif action == 'jiotv_play':
        channel_id = params.get('channel_id')
        jiotv.play_channel(HANDLE, channel_id)
    elif action == 'jiotv_login':
        jiotv.login()
    elif action == 'coming_soon':
        show_coming_soon()
    elif action == 'settings':
        open_settings()
    else:
        log(f"Unknown action: {action}", xbmc.LOGWARNING)
        show_main_menu()


def main():
    """Main entry point."""
    log(f"RevTV {ADDON_VERSION} started")
    params = dict(parse_qsl(sys.argv[2][1:]))
    router(params)


if __name__ == '__main__':
    main()
