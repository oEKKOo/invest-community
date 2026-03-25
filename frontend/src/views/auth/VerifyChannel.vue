<template>
  <div class="verify-page">
    <el-card class="verify-card">
      <h2>基础认证</h2>
      <el-form :model="form" label-width="90px">
        <el-form-item label="认证渠道">
          <el-radio-group v-model="form.channel">
            <el-radio label="EMAIL">邮箱</el-radio>
            <el-radio label="PHONE">手机号</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item :label="form.channel === 'EMAIL' ? '邮箱' : '手机号'">
          <el-input v-model="form.target" />
        </el-form-item>
        <el-form-item label="验证码">
          <el-input v-model="form.code">
            <template #append>
              <el-button @click="sendCode">发送验证码</el-button>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="confirmCode">确认认证</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { sendVerificationCode, confirmVerificationCode } from '../../api/auth'
import { useAuthStore } from '../../stores/auth'

const authStore = useAuthStore()
const form = reactive({
  channel: 'EMAIL' as 'EMAIL' | 'PHONE',
  target: '',
  code: ''
})

const sendCode = async () => {
  await sendVerificationCode({
    channel: form.channel,
    target: form.target,
    purpose: 'VERIFY_CONTACT'
  })
  ElMessage.success('验证码已发送')
}

const confirmCode = async () => {
  await confirmVerificationCode({
    channel: form.channel,
    target: form.target,
    purpose: 'VERIFY_CONTACT',
    code: form.code
  })
  await authStore.fetchCurrentUser()
  ElMessage.success('基础认证完成')
}
</script>

<style scoped>
.verify-page { padding: 20px; }
.verify-card { max-width: 520px; margin: 0 auto; }
</style>

