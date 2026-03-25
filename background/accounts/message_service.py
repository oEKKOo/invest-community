import base64
import logging
from datetime import datetime, timedelta
from email.utils import parseaddr

import requests
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def send_email_verification_code(email: str, code: str, minutes: int = 10) -> None:
    subject = 'InvestHub 注册/登录验证码'
    body = f'您的验证码是：{code}，{minutes}分钟内有效。'
    from_email = (
        getattr(settings, 'EMAIL_FROM', None)
        or getattr(settings, 'DEFAULT_FROM_EMAIL', None)
        or getattr(settings, 'EMAIL_HOST_USER', None)
    )
    sender_addr = parseaddr(from_email or '')[1]
    if not sender_addr:
        raise ValueError('邮件发送配置无效：EMAIL_FROM/DEFAULT_FROM_EMAIL 为空或格式不正确')
    recv_addr = parseaddr(email or '')[1]
    if not recv_addr:
        raise ValueError('收件邮箱格式不正确')
    send_mail(subject, body, from_email, [email], fail_silently=False)


def send_sms_verification_code(phone: str, code: str, minutes: int = 10) -> None:
    provider = (getattr(settings, 'SMS_PROVIDER', 'MOCK') or 'MOCK').upper()

    if provider == 'TWILIO':
        _send_sms_via_twilio(phone, code, minutes)
        return

    if provider == 'HTTP':
        _send_sms_via_http_gateway(phone, code, minutes)
        return

    # 开发环境默认 mock：打印日志而不真实发送
    logger.warning('SMS_PROVIDER=%s, 使用 MOCK 短信发送。phone=%s code=%s', provider, phone, code)


def _send_sms_via_twilio(phone: str, code: str, minutes: int) -> None:
    sid = getattr(settings, 'TWILIO_ACCOUNT_SID', '')
    token = getattr(settings, 'TWILIO_AUTH_TOKEN', '')
    from_phone = getattr(settings, 'TWILIO_FROM_PHONE', '')
    if not sid or not token or not from_phone:
        raise ValueError('Twilio 配置缺失，请检查 TWILIO_ACCOUNT_SID/TWILIO_AUTH_TOKEN/TWILIO_FROM_PHONE')

    url = f'https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json'
    msg = f'Your verification code is {code}. It expires in {minutes} minutes.'
    auth = base64.b64encode(f'{sid}:{token}'.encode('utf-8')).decode('utf-8')
    headers = {'Authorization': f'Basic {auth}'}
    data = {'To': phone, 'From': from_phone, 'Body': msg}
    resp = requests.post(url, headers=headers, data=data, timeout=15)
    if resp.status_code >= 300:
        raise ValueError(f'Twilio 发送失败: {resp.status_code} {resp.text}')


def _send_sms_via_http_gateway(phone: str, code: str, minutes: int) -> None:
    url = getattr(settings, 'SMS_HTTP_URL', '')
    token = getattr(settings, 'SMS_HTTP_TOKEN', '')
    if not url:
        raise ValueError('SMS_HTTP_URL 未配置')

    payload = {
        'phone': phone,
        'code': code,
        'minutes': minutes,
        'scene': 'register_login_verification',
    }
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'

    resp = requests.post(url, json=payload, headers=headers, timeout=15)
    if resp.status_code >= 300:
        raise ValueError(f'短信网关调用失败: {resp.status_code} {resp.text}')

