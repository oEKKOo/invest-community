<template>
  <div class="messages-page">
    <div class="messages-layout">
      <aside class="conversation-list">
        <h2 class="section-title">我的会话</h2>
        <el-skeleton v-if="store.loading && !store.conversations.length" :rows="5" animated />
        <el-empty v-else-if="!store.conversations.length" description="还没有任何私信会话" />
        <ul v-else class="conversation-items">
          <li
            v-for="c in store.conversations"
            :key="c.id"
            class="conversation-item"
            :class="{ active: c.id === store.currentConversationId }"
            @click="handleOpenConversation(c.id)"
          >
            <div class="avatar-stack">
              <el-avatar
                v-for="p in c.participants.slice(0, 2)"
                :key="p.userId"
                :size="26"
                :src="p.avatar"
              >
                {{ p.displayName[0] }}
              </el-avatar>
            </div>
            <div class="conversation-meta">
              <div class="conversation-title">
                {{ c.title || c.participants.map(p => p.displayName).join('、') }}
              </div>
              <div class="conversation-sub">
                {{ c.participants.length }} 人 ·
                {{ c.lastMessageAt ? formatTime(c.lastMessageAt) : '暂无消息' }}
              </div>
            </div>
          </li>
        </ul>
      </aside>

      <section class="message-panel">
        <div v-if="!store.currentConversationId" class="empty-hint">
          <p>选择左侧一个会话开始聊天</p>
        </div>

        <div v-else class="message-thread">
          <div class="messages-scroll">
            <div
              v-for="m in store.messages"
              :key="m.id"
              class="message-item"
              :class="{ mine: m.senderId === authStore.user?.id }"
            >
              <el-avatar :src="m.senderAvatar" :size="30" class="msg-avatar">
                {{ m.senderName[0] }}
              </el-avatar>
              <div class="msg-bubble">
                <div class="msg-header">
                  <span class="msg-name">{{ m.senderName }}</span>
                  <span class="msg-time">{{ formatTime(m.createdAt) }}</span>
                </div>
                <div class="msg-content">
                  {{ m.content }}
                </div>
                <div v-if="m.attachments?.length" class="msg-attachments">
                  <a
                    v-for="att in m.attachments"
                    :key="att.id"
                    :href="att.url"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {{ att.name || `附件#${att.id}` }}
                  </a>
                </div>
              </div>
            </div>
          </div>

          <div class="message-input">
            <el-input
              v-model="draft"
              type="textarea"
              :rows="2"
              resize="none"
              placeholder="输入私信内容，按 Enter 发送"
              @keydown.enter.prevent="handleSend"
            />
            <el-upload
              :auto-upload="false"
              :show-file-list="false"
              accept="image/*"
              :on-change="handleMessageImageSelect"
            >
              <el-button size="small">图片</el-button>
            </el-upload>
            <el-button type="primary" size="small" class="send-btn" @click="handleSend">
              发送
            </el-button>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
import { onMounted, ref } from 'vue'
import { dayjs } from '@/utils/date'
import { useMessagesStore } from '@/stores/messages'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

const store = useMessagesStore()
const authStore = useAuthStore()
const draft = ref('')
const messageAttachmentIds = ref<number[]>([])

const formatTime = (iso: string) => {
  return dayjs(iso).format('MM-DD HH:mm')
}

const handleOpenConversation = async (id: number) => {
  await store.openConversation(id)
}

const handleSend = async () => {
  const text = draft.value.trim()
  if (!text && !messageAttachmentIds.value.length) return
  try {
    await store.sendMessage(text, messageAttachmentIds.value.length ? messageAttachmentIds.value : undefined)
    draft.value = ''
    messageAttachmentIds.value = []
  } catch {
    ElMessage.error('发送失败')
  }
}

const handleMessageImageSelect = async (uploadFile: any) => {
  if (!uploadFile?.raw) return
  try {
    const res = await (await import('@/api/messages')).uploadMessageAttachment(uploadFile.raw as File)
    messageAttachmentIds.value.push(res.id)
    ElMessage.success('图片上传成功')
  } catch {
    ElMessage.error('图片上传失败')
  }
}

onMounted(async () => {
  if (!authStore.isLoggedIn) return
  await store.fetchConversations()
})
</script>

<style scoped lang="scss">
.messages-page {
  max-width: 1100px;
  margin: 0 auto;
}

.messages-layout {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 1rem;
}

.conversation-list {
  background: #fff;
  border-radius: $border-radius;
  border: 1px solid $border-default;
  padding: 1rem;
}

.section-title {
  font-size: 0.9rem;
  font-weight: 700;
  margin-bottom: 0.75rem;
}

.conversation-items {
  list-style: none;
  margin: 0;
  padding: 0;
}

.conversation-item {
  display: flex;
  gap: 0.6rem;
  padding: 0.5rem 0.35rem;
  border-radius: 8px;
  cursor: pointer;

  &:hover {
    background: $bg-surface;
  }

  &.active {
    background: rgba(37, 99, 235, 0.08);
    border: 1px solid rgba(37, 99, 235, 0.3);
  }
}

.avatar-stack {
  display: flex;
  flex-shrink: 0;

  :deep(.el-avatar) {
    margin-left: -6px;

    &:first-child {
      margin-left: 0;
    }
  }
}

.conversation-meta {
  flex: 1;
  overflow: hidden;
}

.conversation-title {
  font-size: 0.85rem;
  font-weight: 600;
  color: $text-primary;
}

.conversation-sub {
  font-size: 0.75rem;
  color: $text-muted;
}

.message-panel {
  background: #fff;
  border-radius: $border-radius;
  border: 1px solid $border-default;
  padding: 1rem;
  min-height: 420px;
  display: flex;
  flex-direction: column;
}

.empty-hint {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: $text-muted;
}

.message-thread {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.messages-scroll {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding-right: 0.25rem;
}

.message-item {
  display: flex;
  gap: 0.5rem;

  &.mine {
    flex-direction: row-reverse;

    .msg-bubble {
      background: rgba(37, 99, 235, 0.08);
    }
  }
}

.msg-avatar {
  flex-shrink: 0;
}

.msg-bubble {
  max-width: 70%;
  padding: 0.5rem 0.75rem;
  border-radius: 10px;
  background: $bg-surface;
}

.msg-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.2rem;
}

.msg-name {
  font-size: 0.8rem;
  font-weight: 600;
}

.msg-time {
  font-size: 0.7rem;
  color: $text-muted;
}

.msg-content {
  font-size: 0.85rem;
  color: $text-primary;
  white-space: pre-wrap;
}

.message-input {
  margin-top: 0.75rem;
  display: flex;
  gap: 0.5rem;
  align-items: flex-end;
}

.send-btn {
  align-self: stretch;
}
</style>

