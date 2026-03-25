<template>
  <div class="pro-page">
    <el-card class="pro-card">
      <h2>专业认证（加V）</h2>
      <el-alert
        v-if="!authStore.authCapabilities.riskAssessed"
        type="warning"
        show-icon
        title="提交专业认证前需要先完成风险评估问卷"
      />
      <el-form :model="form" label-width="130px">
        <el-form-item label="从业资格证明URL">
          <el-input v-model="form.qualification_doc_url" />
        </el-form-item>
        <el-form-item label="学历证明URL">
          <el-input v-model="form.education_doc_url" />
        </el-form-item>
        <el-form-item label="补充材料URL">
          <el-input v-model="form.additional_doc_url" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :disabled="!authStore.authCapabilities.riskAssessed" @click="submit">
            提交专业认证
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { submitProfessionalVerification } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const form = reactive({
  qualification_doc_url: '',
  education_doc_url: '',
  additional_doc_url: ''
})

const submit = async () => {
  await submitProfessionalVerification(form)
  await authStore.fetchCurrentUser()
  ElMessage.success('专业认证申请已提交')
}
</script>

<style scoped>
.pro-page { padding: 20px; }
.pro-card { max-width: 700px; margin: 0 auto; }
</style>

