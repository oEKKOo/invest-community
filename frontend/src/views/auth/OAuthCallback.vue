<template>
  <div class="auth-callback">
    <el-card class="callback-card">
      <h2>第三方登录处理中</h2>
      <p>{{ message }}</p>
      <el-button type="primary" @click="goLogin">返回登录页</el-button>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { oauthCallback } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const message = ref('正在与第三方平台交换令牌...')

const goLogin = () => router.push('/login')

onMounted(async () => {
  const provider = String(route.params.provider || '').toLowerCase() as 'wechat' | 'weibo'
  const code = String(route.query.code || '')
  const state = String(route.query.state || '')
  if (!provider || !code || !state) {
    message.value = '缺少回调参数，无法完成登录。'
    return
  }
  try {
    const data = await oauthCallback(provider, code, state)
    authStore.setAuth(data)
    ElMessage.success('第三方登录成功')
    router.replace('/')
  } catch (error: any) {
    message.value = error?.message || '第三方登录失败'
  }
})
</script>

<style scoped>
.auth-callback { min-height: 100vh; display: flex; align-items: center; justify-content: center; }
.callback-card { width: 420px; text-align: center; }
</style>

