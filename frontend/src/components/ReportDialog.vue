<template>
  <el-dialog
    v-model="visible"
    :title="dialogTitle"
    width="520px"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="100px"
    >
      <!-- 举报对象信息（只读） -->
      <el-form-item label="举报对象">
        <div class="report-target-info">
          <el-tag :type="getTargetTypeTag(targetType)" size="small">
            {{ getTargetTypeText(targetType) }}
          </el-tag>
          <span class="target-summary">{{ targetSummary }}</span>
        </div>
      </el-form-item>

      <!-- 举报类型 -->
      <el-form-item label="举报类型" prop="reportType">
        <el-select
          v-model="form.reportType"
          placeholder="请选择举报类型"
          style="width: 100%"
        >
          <el-option label="广告/垃圾信息" value="AD" />
          <el-option label="辱骂/人身攻击" value="ABUSE" />
          <el-option label="虚假收益/诱导荐股" value="FAKE_RETURN" />
          <el-option label="违法违规内容" value="ILLEGAL" />
          <el-option label="违规私信/骚扰" value="HARASSMENT" />
          <el-option label="其他" value="OTHER" />
        </el-select>
      </el-form-item>

      <!-- 详细说明 -->
      <el-form-item label="详细说明" prop="reason">
        <el-input
          v-model="form.reason"
          type="textarea"
          :rows="4"
          placeholder="请详细描述举报原因，便于管理员处理"
          maxlength="500"
          show-word-limit
        />
      </el-form-item>

      <!-- 证据上传（可选） -->
      <el-form-item label="证据材料" v-if="showEvidence">
        <el-upload
          v-model:file-list="evidenceFiles"
          :auto-upload="false"
          :limit="3"
          :on-exceed="handleExceed"
          accept="image/*"
          list-type="picture-card"
        >
          <el-icon><Plus /></el-icon>
        </el-upload>
        <div class="upload-tip">
          <el-text type="info" size="small">
            可上传截图等证据材料（最多3张，支持 JPG、PNG 格式）
          </el-text>
        </div>
      </el-form-item>
    </el-form>

    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleClose">取消</el-button>
        <el-button
          type="danger"
          :loading="submitting"
          @click="handleSubmit"
        >
          提交举报
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage, type FormInstance, type FormRules, type UploadFile } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { createReport } from '@/api/reports'
import type { CreateReportParams } from '@/api/reports'

interface Props {
  modelValue: boolean
  targetType: 'POST' | 'COMMENT' | 'USER' | 'PORTFOLIO'
  targetId: number
  targetSummary: string
  showEvidence?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showEvidence: true
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'submitted': []
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const formRef = ref<FormInstance>()
const submitting = ref(false)
const evidenceFiles = ref<UploadFile[]>([])

const form = ref({
  reportType: '',
  reason: ''
})

const rules: FormRules = {
  reportType: [
    { required: true, message: '请选择举报类型', trigger: 'change' }
  ],
  reason: [
    { required: true, message: '请填写详细说明', trigger: 'blur' },
    { min: 10, message: '详细说明至少需要10个字符', trigger: 'blur' }
  ]
}

const dialogTitle = computed(() => {
  const typeMap = {
    POST: '举报帖子',
    COMMENT: '举报评论',
    USER: '举报用户',
    PORTFOLIO: '举报组合'
  }
  return typeMap[props.targetType] || '举报'
})

type TagType = 'danger' | 'warning' | 'primary' | 'info' | 'success'

const getTargetTypeTag = (type: string): TagType => {
  const map: Record<string, TagType> = {
    POST: 'primary',
    COMMENT: 'success',
    USER: 'warning',
    PORTFOLIO: 'info'
  }
  return map[type] ?? 'info'
}

const getTargetTypeText = (type: string) => {
  const map: Record<string, string> = {
    POST: '帖子',
    COMMENT: '评论',
    USER: '用户',
    PORTFOLIO: '组合'
  }
  return map[type] || '未知'
}

const handleExceed = () => {
  ElMessage.warning('最多只能上传3张图片')
}

const handleClose = () => {
  visible.value = false
  form.value = {
    reportType: '',
    reason: ''
  }
  evidenceFiles.value = []
  formRef.value?.clearValidate()
}

const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
  } catch {
    return
  }

  submitting.value = true
  try {
    // 处理证据文件（如果有）
    let evidence: any = null
    if (evidenceFiles.value.length > 0) {
      // 这里可以上传图片到服务器获取URL，暂时先存文件信息
      // 实际项目中应该先上传图片，获取URL后再提交举报
      evidence = {
        images: evidenceFiles.value.map(file => ({
          name: file.name,
          url: file.url || (file.raw ? URL.createObjectURL(file.raw) : '')
        }))
      }
    }

    const params: CreateReportParams = {
      targetType: props.targetType,
      targetId: props.targetId,
      reason: form.value.reason.trim(),
      reportTypeDetail: form.value.reportType,
      evidence
    }

    await createReport(params)
    ElMessage.success('举报已提交，感谢你的反馈。管理员会在24小时内处理')
    emit('submitted')
    handleClose()
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.message || '举报提交失败，请稍后重试')
  } finally {
    submitting.value = false
  }
}

// 监听对话框打开，重置表单
watch(visible, (val) => {
  if (val) {
    form.value = {
      reportType: '',
      reason: ''
    }
    evidenceFiles.value = []
    formRef.value?.clearValidate()
  }
})
</script>

<style lang="scss" scoped>
.report-target-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem;
  background: rgba(15, 23, 42, 0.03);
  border-radius: 6px;
}

.target-summary {
  flex: 1;
  font-size: 0.875rem;
  color: $text-secondary;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.upload-tip {
  margin-top: 0.5rem;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}
</style>
