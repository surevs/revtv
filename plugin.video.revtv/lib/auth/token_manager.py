# -*- coding: utf-8 -*-
"""Token Manager for RevTV - Handles credential storage and refresh."""
import xbmcaddon
import time

class TokenManager:
    def __init__(self, service_name):
        self.addon = xbmcaddon.Addon()
        self.service = service_name
    
    def get_token(self):
        return self.addon.getSetting(f'{self.service}_token')
    
    def set_token(self, token, refresh_token=None):
        self.addon.setSetting(f'{self.service}_token', token)
        if refresh_token:
            self.addon.setSetting(f'{self.service}_refresh_token', refresh_token)
        self.addon.setSetting(f'{self.service}_token_time', str(int(time.time())))
    
    def clear_token(self):
        self.addon.setSetting(f'{self.service}_token', '')
        self.addon.setSetting(f'{self.service}_refresh_token', '')
    
    def is_valid(self):
        return bool(self.get_token())
