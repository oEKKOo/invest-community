import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Group, GroupFile, GroupInvite, GroupJoinRequest, GroupMember, GroupPost, GroupReviewer } from '@/types'
import * as groupsApi from '@/api/groups'

export const useGroupsStore = defineStore('groups', () => {
  const loading = ref(false)
  const groups = ref<Group[]>([])
  const total = ref(0)
  const currentGroup = ref<Group | null>(null)
  const members = ref<GroupMember[]>([])
  const posts = ref<GroupPost[]>([])
  const files = ref<GroupFile[]>([])
  const joinRequests = ref<GroupJoinRequest[]>([])
  const reviewers = ref<GroupReviewer[]>([])
  const invites = ref<GroupInvite[]>([])
  const accessDeniedReason = ref('')

  const fetchGroups = async (params?: { page?: number; pageSize?: number; q?: string; visibility?: 'PUBLIC' | 'PRIVATE' | 'APPROVAL' }) => {
    loading.value = true
    try {
      const res = await groupsApi.getGroups(params)
      groups.value = res.items
      total.value = res.total
      return res
    } finally {
      loading.value = false
    }
  }

  const fetchGroupDetail = async (groupId: number) => {
    currentGroup.value = await groupsApi.getGroupDetail(groupId)
    return currentGroup.value
  }

  const fetchGroupMembers = async (groupId: number) => {
    const res = await groupsApi.getGroupMembers(groupId)
    members.value = res.items
    return res
  }

  const fetchGroupPosts = async (groupId: number) => {
    const res = await groupsApi.getGroupPosts(groupId, { page: 1, pageSize: 50 })
    posts.value = res.items
    return res
  }

  const fetchGroupFiles = async (groupId: number) => {
    const res = await groupsApi.getGroupFiles(groupId)
    files.value = res.items
    return res
  }

  const fetchJoinRequests = async (groupId: number, status?: 'PENDING' | 'APPROVED' | 'REJECTED' | 'CANCELLED') => {
    const res = await groupsApi.getGroupJoinRequests(groupId, status ? { status } : undefined)
    joinRequests.value = res.items
    return res
  }

  const reviewJoinRequest = async (groupId: number, requestId: number, action: 'APPROVE' | 'REJECT', reviewNote?: string) => {
    await groupsApi.reviewGroupJoinRequest(groupId, requestId, { action, reviewNote })
  }

  const fetchReviewers = async (groupId: number) => {
    const res = await groupsApi.getGroupReviewers(groupId)
    reviewers.value = res.items
    return res
  }

  const addReviewer = async (groupId: number, userId: number) => {
    await groupsApi.addGroupReviewer(groupId, userId)
    return fetchReviewers(groupId)
  }

  const removeReviewer = async (groupId: number, userId: number) => {
    await groupsApi.removeGroupReviewer(groupId, userId)
    return fetchReviewers(groupId)
  }

  const fetchInvites = async (groupId: number) => {
    const res = await groupsApi.getGroupInvites(groupId)
    invites.value = res.items
    return res
  }

  const fetchMyInvites = async (status?: 'PENDING' | 'ACCEPTED' | 'REJECTED' | 'CANCELLED') => {
    const res = await groupsApi.getMyGroupInvites(status ? { status } : undefined)
    invites.value = res.items
    return res
  }

  const inviteMember = async (groupId: number, inviteeId: number, message?: string) => {
    await groupsApi.createGroupInvite(groupId, { inviteeId, message })
  }

  const respondInvite = async (groupId: number, inviteId: number, action: 'ACCEPT' | 'REJECT') => {
    await groupsApi.respondGroupInvite(groupId, inviteId, action)
  }

  return {
    loading,
    groups,
    total,
    currentGroup,
    members,
    posts,
    files,
    joinRequests,
    reviewers,
    invites,
    accessDeniedReason,
    fetchGroups,
    fetchGroupDetail,
    fetchGroupMembers,
    fetchGroupPosts,
    fetchGroupFiles,
    fetchJoinRequests,
    reviewJoinRequest,
    fetchReviewers,
    addReviewer,
    removeReviewer,
    fetchInvites,
    fetchMyInvites,
    inviteMember,
    respondInvite,
  }
})
