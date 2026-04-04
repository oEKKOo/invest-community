<template>
  <el-drawer
    :model-value="modelValue"
    title="通知中心"
    size="360px"
    direction="rtl"
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <div class="notif-drawer-body">
      <div class="notif-drawer-header">
        <h3>最新通知</h3>
        <el-button
          v-if="items.length"
          type="text"
          size="small"
          @click="$emit('markAllRead')"
        >
          全部标记已读
        </el-button>
      </div>

      <el-skeleton v-if="loading" :rows="4" animated />

      <el-empty
        v-else-if="!items.length"
        description="暂时没有通知"
      />

      <div v-else class="notif-list">
        <div
          v-for="item in items"
          :key="item.id"
          class="notif-item"
          :class="{ unread: !item.is_read }"
          @click="$emit('notificationClick', item)"
        >
          <div class="notif-main">
            <div class="notif-title-row">
              <span class="notif-tag" :class="`type-${item.notification_type.toLowerCase()}`">
                {{ getNotificationTypeLabel(item.notification_type) }}
              </span>
              <span class="notif-time">{{ formatTime(item.created_at) }}</span>
            </div>
            <div class="notif-title">{{ item.title }}</div>
            <div class="notif-content">{{ item.content }}</div>
          </div>
          <div class="notif-status-dot" v-if="!item.is_read"></div>
        </div>
      </div>
    </div>
  </el-drawer>
</template>

<script setup lang="ts">
import type { Notification } from '@/types'

defineProps<{
  modelValue: boolean
  items: Notification[]
  loading: boolean
}>()

defineEmits<{
  'update:modelValue': [v: boolean]
  markAllRead: []
  notificationClick: [item: Notification]
}>()

const getNotificationTypeLabel = (type: string) => {
  switch (type) {
    case 'LIKE':
      return '点赞'
    case 'COMMENT':
      return '评论'
    case 'FOLLOW':
      return '关注'
    case 'REVIEW_RESULT':
      return '审核'
    case 'SYSTEM':
      return '系统'
    default:
      return '通知'
  }
}

const formatTime = (iso: string) => {
  const d = new Date(iso)
  return `${d.getMonth() + 1}-${d.getDate()} ${d.getHours().toString().padStart(2, '0')}:${d
    .getMinutes()
    .toString()
    .padStart(2, '0')}`
}
</script>

<style lang="scss" scoped>
.notif-drawer-body {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.notif-drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: $apple-space-4;

  h3 {
    margin: 0;
    font-size: $apple-font-body;
    font-weight: 600;
    color: $apple-text-primary;
    font-family: $apple-font-family;
  }
}

.notif-list {
  display: flex;
  flex-direction: column;
  gap: $apple-space-3;
  max-height: 100%;
  overflow-y: auto;
}

.notif-item {
  position: relative;
  padding: $apple-space-4;
  border-radius: $apple-radius-sm;
  border: 1px solid $apple-border-light;
  background: $apple-bg-elevated;
  backdrop-filter: $apple-glass-blur;
  -webkit-backdrop-filter: $apple-glass-blur;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    border-color: $apple-accent;
    box-shadow: $apple-shadow-sm;
  }

  &.unread {
    background: rgba(0, 113, 227, 0.04);
    border-color: rgba(0, 113, 227, 0.15);
  }
}

.notif-main {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.notif-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.15rem;
}

.notif-tag {
  font-size: 0.675rem;
  padding: 2px 6px;
  border-radius: 999px;
  font-weight: 600;
}

.notif-tag.type-like {
  background: rgba(249, 115, 22, 0.08);
  color: #ea580c;
}

.notif-tag.type-comment {
  background: rgba(59, 130, 246, 0.08);
  color: #2563eb;
}

.notif-tag.type-follow {
  background: rgba(16, 185, 129, 0.08);
  color: #059669;
}

.notif-tag.type-review_result {
  background: rgba(234, 179, 8, 0.08);
  color: #ca8a04;
}

.notif-tag.type-system {
  background: rgba(148, 163, 184, 0.12);
  color: #4b5563;
}

.notif-time {
  font-size: $apple-font-caption;
  color: $apple-text-tertiary;
  font-family: $apple-font-family;
}

.notif-title {
  font-size: $apple-font-body;
  font-weight: 600;
  color: $apple-text-primary;
  font-family: $apple-font-family;
}

.notif-content {
  font-size: $apple-font-body;
  color: $apple-text-secondary;
  font-family: $apple-font-family;
}

.notif-status-dot {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: $accent-color;
  box-shadow: 0 0 0 3px rgba(34, 197, 94, 0.25);
}
</style>
