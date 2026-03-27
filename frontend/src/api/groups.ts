import { del, get, patch, post } from './index'
import type {
  Group,
  GroupFile,
  GroupInvite,
  GroupJoinRequest,
  GroupMember,
  GroupPost,
  GroupReviewer,
  PaginatedResponse
} from '@/types'

export interface GroupsQuery {
  q?: string
  visibility?: 'PUBLIC' | 'PRIVATE' | 'APPROVAL'
  page?: number
  pageSize?: number
}

export interface GroupCreatePayload {
  name: string
  description?: string
  avatar?: string
  tags?: string[]
  topicDirection?: string
  visibility: 'PUBLIC' | 'PRIVATE' | 'APPROVAL'
}

export const getGroups = (params?: GroupsQuery): Promise<PaginatedResponse<Group>> =>
  get('/groups/', { params })

export const createGroup = (payload: GroupCreatePayload): Promise<Group> =>
  post('/groups/', payload)

export const getGroupDetail = (groupId: number): Promise<Group> =>
  get(`/groups/${groupId}/`)

export const updateGroup = (groupId: number, payload: Partial<GroupCreatePayload>): Promise<Group> =>
  patch(`/groups/${groupId}/`, payload)

export const dissolveGroup = (groupId: number): Promise<void> =>
  del(`/groups/${groupId}/`)

export const joinGroup = (groupId: number, message?: string): Promise<any> =>
  post(`/groups/${groupId}/join/`, { message })

export const leaveGroup = (groupId: number): Promise<void> =>
  post(`/groups/${groupId}/leave/`)

export const getGroupMembers = (groupId: number): Promise<{ items: GroupMember[]; total: number }> =>
  get(`/groups/${groupId}/members/`)

export const setGroupAdmin = (groupId: number, userId: number): Promise<void> =>
  post(`/groups/${groupId}/members/${userId}/role/`, { action: 'set_admin' })

export const removeGroupAdmin = (groupId: number, userId: number): Promise<void> =>
  post(`/groups/${groupId}/members/${userId}/role/`, { action: 'remove_admin' })

export const removeGroupMember = (groupId: number, userId: number): Promise<void> =>
  post(`/groups/${groupId}/members/${userId}/role/`, { action: 'remove_member' })

export const transferGroupOwner = (groupId: number, targetUserId: number): Promise<void> =>
  post(`/groups/${groupId}/transfer-owner/`, { targetUserId })

export const getGroupJoinRequests = (
  groupId: number,
  params?: { status?: 'PENDING' | 'APPROVED' | 'REJECTED' | 'CANCELLED' }
): Promise<{ items: GroupJoinRequest[]; total: number }> => get(`/groups/${groupId}/join-requests/`, { params })

export const reviewGroupJoinRequest = (
  groupId: number,
  requestId: number,
  payload: { action: 'APPROVE' | 'REJECT'; reviewNote?: string }
): Promise<void> => post(`/groups/${groupId}/join-requests/${requestId}/review/`, payload)

export const getGroupReviewers = (groupId: number): Promise<{ items: GroupReviewer[]; total: number }> =>
  get(`/groups/${groupId}/reviewers/`)

export const addGroupReviewer = (groupId: number, userId: number): Promise<GroupReviewer> =>
  post(`/groups/${groupId}/reviewers/`, { userId })

export const removeGroupReviewer = (groupId: number, userId: number): Promise<void> =>
  del(`/groups/${groupId}/reviewers/${userId}/`)

export const getGroupInvites = (groupId: number): Promise<{ items: GroupInvite[]; total: number }> =>
  get(`/groups/${groupId}/invites/`)

export const getMyGroupInvites = (
  params?: { status?: 'PENDING' | 'ACCEPTED' | 'REJECTED' | 'CANCELLED' }
): Promise<{ items: GroupInvite[]; total: number }> => get('/groups/my-invites/', { params })

export const createGroupInvite = (groupId: number, payload: { inviteeId: number; message?: string }): Promise<GroupInvite> =>
  post(`/groups/${groupId}/invites/`, payload)

export const respondGroupInvite = (groupId: number, inviteId: number, action: 'ACCEPT' | 'REJECT'): Promise<void> =>
  post(`/groups/${groupId}/invites/${inviteId}/respond/`, { action })

export const getGroupPosts = (
  groupId: number,
  params?: { page?: number; pageSize?: number }
): Promise<PaginatedResponse<GroupPost>> => get(`/groups/${groupId}/posts/`, { params })

export const createGroupPost = (
  groupId: number,
  payload: { title: string; body: string; content_type?: 'NORMAL' | 'LONGFORM' | 'POLL' }
): Promise<GroupPost> => post(`/groups/${groupId}/posts/`, payload)

export const getGroupFiles = (groupId: number): Promise<{ items: GroupFile[]; total: number }> =>
  get(`/groups/${groupId}/files/`)

export const uploadGroupFile = (groupId: number, file: File): Promise<GroupFile> => {
  const form = new FormData()
  form.append('file', file)
  return post(`/groups/${groupId}/files/`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export const deleteGroupFile = (groupId: number, fileId: number): Promise<void> =>
  del(`/groups/${groupId}/files/${fileId}/`)
