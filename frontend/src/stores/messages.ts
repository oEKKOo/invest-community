import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as messagesApi from '@/api/messages'
import type { Conversation, Message } from '@/api/messages'

export const useMessagesStore = defineStore('messages', () => {
  const conversations = ref<Conversation[]>([])
  const currentConversationId = ref<number | null>(null)
  const messages = ref<Message[]>([])
  const loading = ref(false)

  const fetchConversations = async () => {
    loading.value = true
    try {
      const res = await messagesApi.getConversations()
      conversations.value = res.items
    } finally {
      loading.value = false
    }
  }

  const openConversation = async (conversationId: number) => {
    currentConversationId.value = conversationId
    loading.value = true
    try {
      const res = await messagesApi.getConversationMessages(conversationId)
      messages.value = res.items
    } finally {
      loading.value = false
    }
  }

  const sendMessage = async (content: string, attachmentIds?: number[]) => {
    if (!currentConversationId.value) return
    const msg = await messagesApi.sendMessage(currentConversationId.value, content, attachmentIds)
    messages.value.push(msg)
  }

  return {
    conversations,
    currentConversationId,
    messages,
    loading,
    fetchConversations,
    openConversation,
    sendMessage
  }
})

