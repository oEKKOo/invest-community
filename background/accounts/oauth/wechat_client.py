from urllib.parse import urlencode
import requests


class WeChatOAuthClient:
    AUTHORIZE_URL = "https://open.weixin.qq.com/connect/qrconnect"
    TOKEN_URL = "https://api.weixin.qq.com/sns/oauth2/access_token"
    USERINFO_URL = "https://api.weixin.qq.com/sns/userinfo"

    def __init__(self, app_id: str, app_secret: str, redirect_uri: str):
        self.app_id = app_id
        self.app_secret = app_secret
        self.redirect_uri = redirect_uri

    def build_authorize_url(self, state: str) -> str:
        query = urlencode({
            "appid": self.app_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": "snsapi_login",
            "state": state,
        })
        return f"{self.AUTHORIZE_URL}?{query}#wechat_redirect"

    def exchange_code(self, code: str) -> dict:
        resp = requests.get(self.TOKEN_URL, params={
            "appid": self.app_id,
            "secret": self.app_secret,
            "code": code,
            "grant_type": "authorization_code",
        }, timeout=10)
        data = resp.json()
        if "errcode" in data:
            raise ValueError(f"WeChat token exchange failed: {data.get('errmsg', 'unknown')}")
        return data

    def fetch_userinfo(self, access_token: str, openid: str) -> dict:
        resp = requests.get(self.USERINFO_URL, params={
            "access_token": access_token,
            "openid": openid,
            "lang": "zh_CN",
        }, timeout=10)
        data = resp.json()
        if "errcode" in data:
            raise ValueError(f"WeChat userinfo failed: {data.get('errmsg', 'unknown')}")
        return data

