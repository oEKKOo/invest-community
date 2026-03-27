<template>
  <div class="groups-page">
    <div class="page-header">
      <div>
        <h2>投资主题群组</h2>
        <p>创建或加入你感兴趣的投资群组</p>
      </div>
      <div class="header-actions">
        <el-button @click="goMyInvites">我的群邀请</el-button>
        <el-button type="primary" @click="showCreate = true">创建群组</el-button>
      </div>
    </div>

    <div class="filters">
      <el-input v-model="keyword" placeholder="搜索群组" @keyup.enter="fetchData" />
      <el-select v-model="visibility" clearable placeholder="可见性" @change="fetchData">
        <el-option label="公开" value="PUBLIC" />
        <el-option label="私密" value="PRIVATE" />
        <el-option label="审核加入" value="APPROVAL" />
      </el-select>
      <el-button @click="fetchData">查询</el-button>
    </div>

    <el-row :gutter="16" v-loading="groupsStore.loading">
      <el-col v-for="g in groupsStore.groups" :key="g.id" :span="8">
        <el-card class="group-card" @click="$router.push(`/groups/${g.id}`)">
          <h3>{{ g.name }}</h3>
          <p class="desc">{{ g.description || '暂无简介' }}</p>
          <div class="meta">
            <span>{{ g.memberCount }} 成员</span>
            <span>{{ g.postCount }} 讨论</span>
            <el-tag size="small">{{ visibilityText(g.visibility) }}</el-tag>
          </div>
          <p class="hint">{{ actionHint(g.visibility) }}</p>
          <div class="actions">
            <el-button
              v-if="g.visibility === 'PUBLIC'"
              size="small"
              type="primary"
              @click.stop="quickJoin(g.id, 'PUBLIC')"
            >
              加入群组
            </el-button>
            <el-button
              v-else-if="g.visibility === 'APPROVAL'"
              size="small"
              type="warning"
              @click.stop="quickJoin(g.id, 'APPROVAL')"
            >
              申请加入
            </el-button>
            <el-button v-else size="small" disabled @click.stop>需邀请加入</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-empty v-if="!groupsStore.loading && groupsStore.groups.length === 0" description="暂无群组" />

    <el-dialog v-model="showCreate" title="创建群组" width="520px">
      <el-form :model="createForm" label-width="90px">
        <el-form-item label="群名称">
          <el-input v-model="createForm.name" />
        </el-form-item>
        <el-form-item label="群简介">
          <el-input v-model="createForm.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="主题方向">
          <el-input v-model="createForm.topicDirection" placeholder="如：价值投资、ETF 轮动" />
        </el-form-item>
        <el-form-item label="可见性">
          <el-select v-model="createForm.visibility">
            <el-option label="公开" value="PUBLIC" />
            <el-option label="私密" value="PRIVATE" />
            <el-option label="审核加入" value="APPROVAL" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="submitCreate">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useGroupsStore } from '../stores/groups'
import { createGroup, joinGroup } from '../api/groups'

const groupsStore = useGroupsStore()
const router = useRouter()
const keyword = ref('')
const visibility = ref<'PUBLIC' | 'PRIVATE' | 'APPROVAL' | undefined>()
const showCreate = ref(false)
const creating = ref(false)
const createForm = ref({
  name: '',
  description: '',
  topicDirection: '',
  visibility: 'PUBLIC' as 'PUBLIC' | 'PRIVATE' | 'APPROVAL',
})

const fetchData = async () => {
  await groupsStore.fetchGroups({
    page: 1,
    pageSize: 30,
    q: keyword.value || undefined,
    visibility: visibility.value,
  })
}

const submitCreate = async () => {
  if (!createForm.value.name.trim()) {
    ElMessage.warning('请输入群名称')
    return
  }
  creating.value = true
  try {
    await createGroup(createForm.value)
    ElMessage.success('群组创建成功')
    showCreate.value = false
    createForm.value = { name: '', description: '', topicDirection: '', visibility: 'PUBLIC' }
    await fetchData()
  } finally {
    creating.value = false
  }
}

const visibilityText = (value: string) => {
  if (value === 'PUBLIC') return '公开'
  if (value === 'PRIVATE') return '私密'
  return '审核'
}

const actionHint = (visibilityValue: string) => {
  if (visibilityValue === 'PRIVATE') return '仅群主邀请加入'
  if (visibilityValue === 'APPROVAL') return '需申请并等待审核'
  return '可直接加入并浏览群内容'
}

const quickJoin = async (groupId: number, visibilityValue: 'PUBLIC' | 'APPROVAL') => {
  await joinGroup(groupId)
  ElMessage.success(visibilityValue === 'APPROVAL' ? '申请已提交' : '加入成功')
}

const goMyInvites = () => {
  router.push('/groups/invites')
}

onMounted(fetchData)
</script>

<style scoped>
.groups-page { max-width: 1100px; margin: 0 auto; }
.page-header { display: flex; justify-content: space-between; margin-bottom: 16px; }
.header-actions { display: flex; gap: 10px; }
.filters { display: flex; gap: 12px; margin-bottom: 16px; }
.group-card { margin-bottom: 16px; cursor: pointer; }
.desc { color: #666; min-height: 40px; }
.meta { display: flex; gap: 12px; align-items: center; }
.hint { margin: 10px 0 0; color: #999; font-size: 12px; }
.actions { margin-top: 12px; display: flex; justify-content: flex-end; }
</style>
