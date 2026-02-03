<template>
  <div class="login-page">
    <div class="login-container">
      <div class="login-header">
        <div class="logo">
          <div class="logo-icon">IH</div>
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
                  placeholder="用户名 / 邮箱"
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
    
    ElMessage.success('登录成功！')
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
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
}

.login-container {
  width: 100%;
  max-width: 400px;
}

.login-header {
  text-align: center;
  margin-bottom: 2rem;
}

.logo {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
}

.logo-icon {
  width: 3rem;
  height: 3rem;
  background: white;
  border-radius: 0.75rem;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #2563eb;
  font-weight: bold;
  font-size: 1.25rem;
}

.logo-text {
  font-size: 2rem;
  font-weight: bold;
  color: white;
  margin: 0;
}

.subtitle {
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.875rem;
  margin: 0;
}

.login-card {
  border: none;
  border-radius: 1rem;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);

  :deep(.el-card__body) {
    padding: 2rem;
  }
}

.login-tabs {
  :deep(.el-tabs__header) {
    margin-bottom: 2rem;
  }

  :deep(.el-tabs__nav-wrap::after) {
    display: none;
  }

  :deep(.el-tabs__item) {
    font-weight: 600;
    font-size: 1rem;
    color: #6b7280;

    &.is-active {
      color: #2563eb;
    }
  }

  :deep(.el-tabs__active-bar) {
    background-color: #2563eb;
  }
}

.login-form,
.register-form {
  :deep(.el-form-item) {
    margin-bottom: 1.5rem;
  }

  :deep(.el-input__wrapper) {
    border-radius: 0.5rem;
    transition: all 0.2s ease-in-out;

    &:hover,
    &.is-focus {
      box-shadow: 0 0 0 1px #2563eb;
    }
  }

  :deep(.el-input__prefix) {
    color: #9ca3af;
  }
}

.login-btn,
.register-btn {
  width: 100%;
  height: 48px;
  border-radius: 0.5rem;
  font-weight: 600;
  font-size: 1rem;
}

.login-footer {
  text-align: center;
  margin-top: 2rem;

  p {
    color: rgba(255, 255, 255, 0.7);
    font-size: 0.875rem;
    margin: 0;
  }
}
</style>