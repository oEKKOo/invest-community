import { get, patch, post, put } from './index'
import type { User, LoginResponse } from '../types'

// 用户注册
export interface RegisterParams {
  username: string
  email: string
  password: string
  password_confirm: string
  phone?: string
}

// 注册接口返回的原始格式（扁平化）
export interface RegisterResponse {
  id: number
  username: string
  displayName: string
  role: 'USER' | 'MODERATOR' | 'ADMIN'
  access: string
  refresh: string
}

export const register = (params: RegisterParams): Promise<RegisterResponse> => {
  return post('/auth/register/', params)
}

// 用户登录
export interface LoginParams {
  username?: string
  identifier?: string
  password: string
}

export const login = (params: LoginParams): Promise<LoginResponse> => {
  return post('/auth/login/', params)
}

export interface PasswordLoginParams {
  identifier: string
  password: string
}

export const loginWithPassword = (params: PasswordLoginParams): Promise<LoginResponse> => {
  return post('/auth/login/password/', params)
}

export interface SmsLoginParams {
  phone: string
  code: string
}

export const loginWithSms = (params: SmsLoginParams): Promise<LoginResponse> => {
  return post('/auth/login/sms/', params)
}

export interface EmailRegisterParams {
  username: string
  email: string
  password: string
  password_confirm: string
  email_code: string
}

export interface PhoneRegisterParams {
  username: string
  phone: string
  email?: string
  password: string
  password_confirm: string
  phone_code: string
}

export const registerEmail = (params: EmailRegisterParams): Promise<LoginResponse> => {
  return post('/auth/register/email/', params)
}

export const registerPhone = (params: PhoneRegisterParams): Promise<LoginResponse> => {
  return post('/auth/register/phone/', params)
}

export interface VerificationSendParams {
  channel: 'EMAIL' | 'PHONE'
  target: string
  purpose: 'REGISTER' | 'LOGIN' | 'PASSWORD_RESET' | 'VERIFY_CONTACT'
}

export const sendVerificationCode = (params: VerificationSendParams): Promise<{ expiresAt: string; debugCode?: string }> => {
  return post('/auth/verification/send/', params)
}

export interface VerificationConfirmParams extends VerificationSendParams {
  code: string
}

export const confirmVerificationCode = (params: VerificationConfirmParams): Promise<void> => {
  return post('/auth/verification/confirm/', params)
}

export const getOAuthStartUrl = (provider: 'wechat' | 'weibo'): Promise<{ authorizeUrl: string; state: string }> => {
  return get(`/auth/oauth/${provider}/start/`)
}

export const oauthCallback = (provider: 'wechat' | 'weibo', code: string, state: string): Promise<LoginResponse> => {
  return get(`/auth/oauth/${provider}/callback/`, { params: { code, state } })
}

export const oauthBind = (
  provider: 'wechat' | 'weibo',
  payload: { provider_uid: string; unionid?: string; openid?: string; access_token?: string; refresh_token?: string }
): Promise<void> => {
  return post(`/auth/oauth/${provider}/bind/`, payload)
}

// 刷新token
export const refreshToken = (refresh: string): Promise<{ access: string }> => {
  return post('/auth/refresh/', { refresh })
}

// 用户登出
export const logout = (): Promise<void> => {
  return post('/auth/logout/')
}

// 获取当前用户信息
export const getCurrentUser = (): Promise<User> => {
  return get('/users/me/')
}

// 更新当前用户信息
export interface UpdateUserParams {
  displayName?: string
  bio?: string
  avatar?: string
  phone?: string
  investmentExperience?: string
}

export const updateCurrentUser = (params: UpdateUserParams): Promise<User> => {
  return patch('/users/me/', params)
}

export interface KycStatus {
  phone_verified: boolean
  email_verified: boolean
  identity_level: 'UNVERIFIED' | 'BASIC' | 'REAL_NAME' | 'PROFESSIONAL'
  real_name_status: 'NONE' | 'PENDING' | 'APPROVED' | 'REJECTED'
  professional_status: 'NONE' | 'PENDING' | 'APPROVED' | 'REJECTED'
  risk_assessment_status: 'NONE' | 'PENDING' | 'APPROVED' | 'REJECTED'
  risk_level?: 'R1' | 'R2' | 'R3' | 'R4' | 'R5' | null
  v_badge: boolean
}

export interface InvestProfile {
  risk_level: 1 | 2 | 3
  horizon: 1 | 2 | 3
  focus_market: string[]
  preferred_assets: string[]
}

export const getKycStatus = (): Promise<KycStatus> => {
  return get('/auth/kyc/status/')
}

export const getInvestProfile = (): Promise<InvestProfile> => {
  return get('/auth/users/me/invest-profile/')
}

export const updateInvestProfile = (params: InvestProfile): Promise<InvestProfile> => {
  return put('/auth/users/me/invest-profile/', params)
}

export const submitRealNameVerification = (params: {
  real_name: string
  id_card_no: string
  face_score?: number
  ocr_passed?: boolean
  liveness_passed?: boolean
}): Promise<{ id: number }> => {
  return post('/auth/kyc/real-name/submit/', params)
}

export const submitProfessionalVerification = (params: {
  qualification_doc_url?: string
  education_doc_url?: string
  additional_doc_url?: string
}): Promise<{ id: number }> => {
  return post('/auth/kyc/professional/submit/', params)
}

export interface RiskQuestionnaire {
  id: number
  version: string
  title: string
  questions: Array<{
    id: number
    text: string
    options: Array<{ label: string; score: number }>
  }>
}

export const getRiskQuestionnaire = (): Promise<RiskQuestionnaire> => {
  return get('/auth/risk/questionnaire/')
}

export const submitRiskQuestionnaire = (params: { template_id?: number; answers: any }): Promise<{ id: number; score: number; riskLevel: string }> => {
  return post('/auth/risk/submit/', params)
}

export const getRiskResult = (): Promise<{ score: number; riskLevel: string; templateVersion: string; createdAt: string }> => {
  return get('/auth/risk/result/')
}