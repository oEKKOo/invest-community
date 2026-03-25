from rest_framework.permissions import BasePermission


class IsBasicVerified(BasePermission):
    message = '需要完成基础认证（手机或邮箱验证）'

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user and user.is_authenticated and (user.phone_verified or user.email_verified)
        )


class IsRealNameVerified(BasePermission):
    message = '需要完成实名认证'

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user and user.is_authenticated and user.real_name_status == 'APPROVED'
        )


class IsProfessionalVerifiedAndRiskAssessed(BasePermission):
    message = '需要完成专业认证且通过风险评估'

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user and user.is_authenticated
            and user.professional_status == 'APPROVED'
            and user.risk_assessment_status == 'APPROVED'
        )

