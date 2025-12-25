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
    
    xbmcplugin.setPluginCategory(HANDLE, ADDON_NAME)
    xbmcplugin.setContent(HANDLE, 'files')
    
    services = [
        {'name': '📺 JioTV', 'action': 'jiotv', 'enabled': True, 'desc': '800+ Live TV Channels'},
        {'name': '🎬 JioHotstar', 'action': 'hotstar', 'enabled': False, 'desc': 'Coming Soon'},
        {'name': '📱 SonyLIV', 'action': 'sonyliv', 'enabled': False, 'desc': 'Coming Soon'},
        {'name': '🌟 Zee5', 'action': 'zee5', 'enabled': False, 'desc': 'Coming Soon'},
        {'name': '🎭 ETV Win', 'action': 'etvwin', 'enabled': False, 'desc': 'Coming Soon'},
        {'name': '☀️ Sun NXT', 'action': 'sunnxt', 'enabled': False, 'desc': 'Coming Soon'},
        {'name': '🎪 Aha', 'action': 'aha', 'enabled': False, 'desc': 'Coming Soon'},
    ]
    
    for service in services:
        if service['enabled']:
            label = f"{service['name']}"
        else:
            label = f"{service['name']} [COLOR gray]({service['desc']})[/COLOR]"
        
        list_item = xbmcgui.ListItem(label=label)
        list_item.setArt({'icon': ADDON_ICON, 'fanart': ADDON_ICON})
        
        if service['enabled']:
            url = get_url(action=service['action'])
            xbmcplugin.addDirectoryItem(HANDLE, url, list_item, isFolder=True)
        else:
            url = get_url(action='coming_soon', service=service['name'])
            xbmcplugin.addDirectoryItem(HANDLE, url, list_item, isFolder=False)
    
    # Separator
    sep = xbmcgui.ListItem(label='─' * 40)
    sep.setProperty('IsPlayable', 'false')
    xbmcplugin.addDirectoryItem(HANDLE, '', sep, isFolder=False)
    
    # Settings
    settings_item = xbmcgui.ListItem(label='⚙️ Settings')
    settings_item.setArt({'icon': ADDON_ICON})
    xbmcplugin.addDirectoryItem(HANDLE, get_url(action='settings'), settings_item, isFolder=False)
    
    xbmcplugin.endOfDirectory(HANDLE)


def show_coming_soon(service_name='This service'):
    """Show coming soon message."""
    show_notification(f"{service_name} is coming soon!", time=3000)


def open_settings():
    """Open addon settings."""
    ADDON.openSettings()


def router(params):
    """Route to the appropriate action based on parameters."""
    action = params.get('action')
    
    log(f"Router action: {action}, params: {params}")
    
    if action is None:
        show_main_menu()
    
    # JioTV routes
    elif action == 'jiotv':
        from lib.services import jiotv
        jiotv.show_menu(HANDLE, get_url)
    elif action == 'jiotv_categories':
        from lib.services import jiotv
        jiotv.show_categories(HANDLE, get_url)
    elif action == 'jiotv_languages':
        from lib.services import jiotv
        jiotv.show_languages(HANDLE, get_url)
    elif action == 'jiotv_channels':
        from lib.services import jiotv
        category = params.get('category')
        language = params.get('language')
        jiotv.show_channels(HANDLE, get_url, category=category, language=language)
    elif action == 'jiotv_play':
        from lib.services import jiotv
        channel_id = params.get('channel_id')
        jiotv.play_channel(HANDLE, channel_id)
    elif action == 'jiotv_login':
        from lib.services import jiotv
        jiotv.login()
    elif action == 'jiotv_logout':
        from lib.services import jiotv
        jiotv.logout()
    
    # Other services (coming soon)
    elif action in ('hotstar', 'sonyliv', 'zee5', 'etvwin', 'sunnxt', 'aha'):
        show_coming_soon(params.get('service', action))
    
    elif action == 'coming_soon':
        show_coming_soon(params.get('service', 'This service'))
    
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
