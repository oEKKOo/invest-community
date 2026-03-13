import { get, post } from './index'

export interface ConversationParticipant {
  userId: number
  username: string
  displayName: string
  avatar: string
}

export interface Conversation {
  id: number
  title?: string
  is_group: boolean
  createdAt: string
  lastMessageAt?: string | null
  participants: ConversationParticipant[]
}

export interface Message {
  id: number
  conversation_id: number
  senderId: number
  senderName: string
  senderAvatar?: string
  content: string
  is_deleted: boolean
  createdAt: string
  isRead: boolean
}

export const getConversations = (): Promise<{ items: Conversation[] }> => {
  return get('/messages/conversations/')
}

export const createConversation = (payload: {
  participantIds: number[]
  title?: string
}): Promise<Conversation> => {
  return post('/messages/conversations/', payload)
}

export const getConversationMessages = (
  conversationId: number
): Promise<{ items: Message[] }> => {
  return get(`/messages/conversations/${conversationId}/messages/`)
}

export const sendMessage = (
  conversationId: number,
  content: string
): Promise<Message> => {
  return post(`/messages/conversations/${conversationId}/messages/`, { content })
}

export const markMessageRead = (messageId: number): Promise<void> => {
  return post(`/messages/${messageId}/read/`)
}

