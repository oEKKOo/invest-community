<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-header">
        <div class="logo">
          <div class="logo-icon">
            <svg width="26" height="26" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M3 17L9 11L13 15L21 7" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M17 7H21V11" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          <h1 class="logo-text">InvestHub</h1>
        </div>
        <p class="subtitle">投资社区 · 共享智慧</p>
      </div>

      <el-card class="login-card">
        <el-tabs v-model="activeTab" class="login-tabs">
          <el-tab-pane label="登录" name="login">
            <el-form
              ref="loginFormRef"
              :model="loginForm"
              :rules="loginRules"
              class="login-form"
              @submit.prevent="handleLogin"
            >
              <el-form-item prop="username">
                <el-input
                  v-model="loginForm.username"
                  placeholder="用户名/ 邮箱"
                  size="large"
                  clearable
                >
                  <template #prefix>
                    <el-icon><User /></el-icon>
                  </template>
                </el-input>
              </el-form-item>

              <el-form-item prop="password">
                <el-input
                  v-model="loginForm.password"
                  type="password"
                  placeholder="密码"
                  size="large"
                  show-password
                  @keyup.enter="handleLogin"
                >
                  <template #prefix>
                    <el-icon><Lock /></el-icon>
                  </template>
                </el-input>
              </el-form-item>

              <el-form-item>
                <el-button
                  type="primary"
                  size="large"
                  class="login-btn"
                  :loading="loading"
                  @click="handleLogin"
                >
                  {{ loading ? '登录中...' : '登录' }}
                </el-button>
              </el-form-item>
            </el-form>
          </el-tab-pane>

          <el-tab-pane label="注册" name="register">
            <el-form
              ref="registerFormRef"
              :model="registerForm"
              :rules="registerRules"
              class="register-form"
              @submit.prevent="handleRegister"
            >
              <el-form-item prop="username">
                <el-input
                  v-model="registerForm.username"
                  placeholder="用户名"
                  size="large"
                  clearable
                >
                  <template #prefix>
                    <el-icon><User /></el-icon>
                  </template>
                </el-input>
              </el-form-item>

              <el-form-item prop="email">
                <el-input
                  v-model="registerForm.email"
                  placeholder="邮箱地址"
                  size="large"
                  clearable
                >
                  <template #prefix>
                    <el-icon><Message /></el-icon>
                  </template>
                </el-input>
              </el-form-item>

              <el-form-item prop="phone">
                <el-input
                  v-model="registerForm.phone"
                  placeholder="手机号（可选）"
                  size="large"
                  clearable
                >
                  <template #prefix>
                    <el-icon><Phone /></el-icon>
                  </template>
                </el-input>
              </el-form-item>

              <el-form-item prop="password">
                <el-input
                  v-model="registerForm.password"
                  type="password"
                  placeholder="密码（至少8位）"
                  size="large"
                  show-password
                >
                  <template #prefix>
                    <el-icon><Lock /></el-icon>
                  </template>
                </el-input>
              </el-form-item>

              <el-form-item prop="password_confirm">
                <el-input
                  v-model="registerForm.password_confirm"
                  type="password"
                  placeholder="确认密码"
                  size="large"
                  show-password
                  @keyup.enter="handleRegister"
                >
                  <template #prefix>
                    <el-icon><Lock /></el-icon>
                  </template>
                </el-input>
              </el-form-item>

              <el-form-item>
                <el-button
                  type="primary"
                  size="large"
                  class="register-btn"
                  :loading="loading"
                  @click="handleRegister"
                >
                  {{ loading ? '注册中...' : '注册账号' }}
                </el-button>
              </el-form-item>
            </el-form>
          </el-tab-pane>
        </el-tabs>
      </el-card>

      <div class="login-footer">
        <p>© 2024 InvestHub Community. 让投资更智慧.</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import {
  User,
  Lock,
  Message,
  Phone
} from '@element-plus/icons-vue'

const router = useRouter()
const authStore = useAuthStore()

const activeTab = ref('login')
const loading = ref(false)

// 表单引用
const loginFormRef = ref<FormInstance>()
const registerFormRef = ref<FormInstance>()

// 登录表单
const loginForm = reactive({
  username: '',
  password: ''
})

// 注册表单
const registerForm = reactive({
  username: '',
  email: '',
  phone: '',
  password: '',
  password_confirm: ''
})

// 登录表单验证规则
const loginRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名或邮箱', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6位', trigger: 'blur' }
  ]
}

// 注册表单验证规则
const registerRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 150, message: '用户名长度3-150字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, message: '密码长度至少8位', trigger: 'blur' }
  ],
  password_confirm: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== registerForm.password) {
          callback(new Error('两次输入密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

// 处理登录
const handleLogin = async () => {
  if (!loginFormRef.value) return

  try {
    await loginFormRef.value.validate()
    loading.value = true
    
    await authStore.login(loginForm)
    
    ElMessage.success('登录成功')
    router.push('/')
  } catch (error: any) {
    if (error.fields) {
      // 表单验证错误
      return
    }
    
    console.error('Login error:', error)
    ElMessage.error(error.message || '登录失败，请检查用户名和密码')
  } finally {
    loading.value = false
  }
}

// 处理注册
const handleRegister = async () => {
  if (!registerFormRef.value) return

  try {
    await registerFormRef.value.validate()
    loading.value = true
    
    await authStore.register(registerForm)
    
    ElMessage.success('注册成功！欢迎加入InvestHub')
    router.push('/')
  } catch (error: any) {
    if (error.fields) {
      // 表单验证错误
      return
    }
    
    console.error('Register error:', error)
    ElMessage.error(error.message || '注册失败，请稍后重试')
  } finally {
    loading.value = false
  }
}
</script>

<style lang="scss" scoped>
.login-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #EFF6FF 0%, #F8FAFC 50%, #F0FDF4 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  position: relative;
  overflow: hidden;
}

// Subtle decorative background elements
.login-page::before {
  content: '';
  position: absolute;
  top: -15%;
  left: -8%;
  width: 500px;
  height: 500px;
  background: radial-gradient(circle, rgba(29, 78, 216, 0.08) 0%, transparent 65%);
  border-radius: 50%;
  pointer-events: none;
}

.login-page::after {
  content: '';
  position: absolute;
  bottom: -15%;
  right: -8%;
  width: 420px;
  height: 420px;
  background: radial-gradient(circle, rgba(22, 163, 74, 0.06) 0%, transparent 65%);
  border-radius: 50%;
  pointer-events: none;
}

.login-container {
  width: 100%;
  max-width: 440px;
  position: relative;
  z-index: 1;
  animation: fadeIn 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

.login-header {
  text-align: center;
  margin-bottom: 2rem;
}

.logo {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.875rem;
  margin-bottom: 0.875rem;
}

.logo-icon {
  width: 52px;
  height: 52px;
  background: $gradient-primary;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: $shadow-blue;
  flex-shrink: 0;
}

.logo-text {
  font-size: 2rem;
  font-weight: 700;
  color: $text-primary;
  margin: 0;
  letter-spacing: -0.03em;
}

.subtitle {
  font-size: 0.875rem;
  color: $text-secondary;
  margin: 0;
  letter-spacing: 0.04em;
  font-weight: 500;
}

.login-card {
  background: #FFFFFF !important;
  border: 1px solid $border-subtle !important;
  border-radius: 20px !important;
  box-shadow: 0 4px 24px rgba(15, 23, 42, 0.08), 0 1px 4px rgba(15, 23, 42, 0.04) !important;
  overflow: hidden;

  :deep(.el-card__body) {
    padding: 2rem;
  }
}

.login-tabs {
  :deep(.el-tabs__header) {
    margin-bottom: 1.75rem;
  }

  :deep(.el-tabs__nav-wrap::after) {
    background-color: $border-subtle !important;
    height: 1px !important;
  }

  :deep(.el-tabs__item) {
    font-weight: 600;
    font-size: 1rem;
    color: $text-muted !important;
    padding: 0 1rem !important;

    &.is-active {
      color: $primary-color !important;
    }

    &:hover:not(.is-active) {
      color: $text-secondary !important;
    }
  }

  :deep(.el-tabs__active-bar) {
    background: $gradient-primary !important;
    height: 2px !important;
    border-radius: 1px !important;
  }
}

.login-form,
.register-form {
  :deep(.el-form-item) {
    margin-bottom: 1.25rem;
  }

  :deep(.el-form-item__error) {
    font-size: 0.75rem;
    margin-top: 0.25rem;
  }

  :deep(.el-input__wrapper) {
    background: $bg-surface !important;
    border: 1px solid $border-default !important;
    border-radius: 10px !important;
    box-shadow: $shadow-sm !important;
    transition: $transition-all !important;
    padding: 0 1rem !important;

    &:hover {
      border-color: $primary-color !important;
      background: #FFFFFF !important;
    }

    &.is-focus {
      border-color: $primary-color !important;
      box-shadow: 0 0 0 3px rgba(29, 78, 216, 0.12) !important;
      background: #FFFFFF !important;
    }
  }

  :deep(.el-input__inner) {
    height: 44px !important;
    font-size: 0.9375rem !important;
    color: $text-primary !important;

    &::placeholder {
      color: $text-muted !important;
    }
  }

  :deep(.el-input__prefix) {
    color: $text-muted !important;
  }

  :deep(.el-input__suffix) {
    color: $text-secondary !important;
  }
}

.login-btn,
.register-btn {
  width: 100%;
  height: 48px;
  border-radius: 12px;
  font-weight: 600;
  font-size: 1rem;
  letter-spacing: 0.02em;
  background: $gradient-primary !important;
  border: none !important;
  box-shadow: $shadow-blue !important;
  transition: $transition-all !important;
  color: #FFFFFF !important;

  &:hover:not(.is-loading) {
    box-shadow: 0 8px 24px rgba(29, 78, 216, 0.4) !important;
    transform: translateY(-1px);
  }

  &:active {
    transform: translateY(0) !important;
  }
}

.login-footer {
  text-align: center;
  margin-top: 1.5rem;

  p {
    color: $text-muted;
    font-size: 0.8rem;
    margin: 0;
  }
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
