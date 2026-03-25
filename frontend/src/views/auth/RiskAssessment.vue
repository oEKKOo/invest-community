<template>
  <div class="risk-page">
    <el-card class="risk-card">
      <h2>{{ questionnaire?.title || '风险评估问卷' }}</h2>
      <template v-if="questionnaire">
        <div v-for="q in questionnaire.questions" :key="q.id" class="question-block">
          <h4>{{ q.text }}</h4>
          <el-radio-group v-model="selected[q.id]">
            <el-radio
              v-for="opt in q.options"
              :key="`${q.id}-${opt.label}`"
              :label="opt.score"
            >
              {{ opt.label }}（{{ opt.score }} 分）
            </el-radio>
          </el-radio-group>
        </div>
        <el-button type="primary" @click="submit">提交问卷</el-button>
      </template>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getRiskQuestionnaire, submitRiskQuestionnaire } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const questionnaire = ref<any>(null)
const selected = reactive<Record<string, number>>({})

onMounted(async () => {
  questionnaire.value = await getRiskQuestionnaire()
})

const submit = async () => {
  await submitRiskQuestionnaire({
    template_id: questionnaire.value.id,
    answers: { selected }
  })
  await authStore.fetchCurrentUser()
  ElMessage.success('风险评估完成')
}
</script>

<style scoped>
.risk-page { padding: 20px; }
.risk-card { max-width: 720px; margin: 0 auto; }
.question-block { margin-bottom: 18px; }
</style>

