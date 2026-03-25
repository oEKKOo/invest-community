from urllib.parse import urlencode
import requests


class WeiboOAuthClient:
    AUTHORIZE_URL = "https://api.weibo.com/oauth2/authorize"
    TOKEN_URL = "https://api.weibo.com/oauth2/access_token"
    USERINFO_URL = "https://api.weibo.com/2/users/show.json"

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    def build_authorize_url(self, state: str) -> str:
        query = urlencode({
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "state": state,
        })
        return f"{self.AUTHORIZE_URL}?{query}"

    def exchange_code(self, code: str) -> dict:
        resp = requests.post(self.TOKEN_URL, data={
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri,
            "code": code,
        }, timeout=10)
        data = resp.json()
        if "error" in data:
            raise ValueError(f"Weibo token exchange failed: {data.get('error_description', data['error'])}")
        return data

    def fetch_userinfo(self, access_token: str, uid: str) -> dict:
        resp = requests.get(self.USERINFO_URL, params={
            "access_token": access_token,
            "uid": uid,
        }, timeout=10)
        data = resp.json()
        if "error" in data:
            raise ValueError(f"Weibo userinfo failed: {data.get('error')}")
        return data

