<template>
  <div class="auth-page">
    <el-card class="auth-card">
      <h2>实名认证</h2>
      <el-form :model="form" label-width="110px">
        <el-form-item label="真实姓名"><el-input v-model="form.real_name" /></el-form-item>
        <el-form-item label="身份证号"><el-input v-model="form.id_card_no" /></el-form-item>
        <el-form-item label="人脸分数"><el-input-number v-model="form.face_score" :min="0" :max="100" /></el-form-item>
        <el-form-item>
          <el-button type="primary" @click="submit">提交实名认证</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { submitRealNameVerification } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const form = reactive({
  real_name: '',
  id_card_no: '',
  face_score: 85
})

const submit = async () => {
  await submitRealNameVerification(form)
  await authStore.fetchCurrentUser()
  ElMessage.success('实名认证申请已提交')
}
</script>

<style scoped>
.auth-page { padding: 20px; }
.auth-card { max-width: 520px; margin: 0 auto; }
</style>

