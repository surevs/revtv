# -*- coding: utf-8 -*-
"""API Client for RevTV - HTTP requests with retry and error handling."""
import requests
import xbmc

class APIClient:
    def __init__(self, timeout=30):
        self.session = requests.Session()
        self.timeout = timeout
    
    def get(self, url, **kwargs):
        kwargs.setdefault('timeout', self.timeout)
        try:
            return self.session.get(url, **kwargs)
        except Exception as e:
            xbmc.log(f"[RevTV] GET error: {e}", xbmc.LOGERROR)
            raise
    
    def post(self, url, **kwargs):
        kwargs.setdefault('timeout', self.timeout)
        try:
            return self.session.post(url, **kwargs)
        except Exception as e:
            xbmc.log(f"[RevTV] POST error: {e}", xbmc.LOGERROR)
            raise
