from django.urls import path
from . import views

urlpatterns = [
    # 认证相关
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('refresh/', views.token_refresh, name='token_refresh'),
    path('logout/', views.logout, name='logout'),  # 新增logout接口
    path('register/email/', views.register_email, name='register_email'),
    path('register/phone/', views.register_phone, name='register_phone'),
    path('login/password/', views.login_password, name='login_password'),
    path('login/sms/', views.login_sms, name='login_sms'),
    path('verification/send/', views.verification_send, name='verification_send'),
    path('verification/confirm/', views.verification_confirm, name='verification_confirm'),
    path('oauth/<str:provider>/start/', views.oauth_start, name='oauth_start'),
    path('oauth/<str:provider>/callback/', views.oauth_callback, name='oauth_callback'),
    path('oauth/<str:provider>/bind/', views.oauth_bind, name='oauth_bind'),
    path('kyc/real-name/submit/', views.submit_real_name, name='submit_real_name'),
    path('kyc/professional/submit/', views.submit_professional, name='submit_professional'),
    path('kyc/status/', views.kyc_status, name='kyc_status'),
    path('risk/questionnaire/', views.risk_questionnaire, name='risk_questionnaire'),
    path('risk/submit/', views.submit_risk_questionnaire, name='submit_risk_questionnaire'),
    path('risk/result/', views.risk_result, name='risk_result'),

    # 投资偏好
    path('users/me/invest-profile/', views.invest_profile, name='invest_profile'),
]