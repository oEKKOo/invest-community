import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Post, PaginatedResponse, PostStatus } from '@/types'
import * as postsApi from '@/api/posts'

export const usePostsStore = defineStore('posts', () => {
  // State
  const posts = ref<Post[]>([])
  const currentPost = ref<Post | null>(null)
  const loading = ref(false)
  const pagination = ref({
    page: 1,
    pageSize: 20,
    total: 0
  })

  // Actions
  const fetchPosts = async (params?: postsApi.GetPostsParams) => {
    loading.value = true
    try {
      const response = await postsApi.getPosts(params)
      posts.value = response.items
      pagination.value = {
        page: response.page,
        pageSize: response.pageSize,
        total: response.total
      }
      return response
    } catch (error) {
      console.error('Failed to fetch posts:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  const fetchPost = async (id: number) => {
    loading.value = true
    try {
      const post = await postsApi.getPost(id)
      currentPost.value = post
      return post
    } catch (error) {
      console.error('Failed to fetch post:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  const createPost = async (params: postsApi.CreatePostParams) => {
    try {
      const newPost = await postsApi.createPost(params)
      posts.value.unshift(newPost)
      return newPost
    } catch (error) {
      console.error('Failed to create post:', error)
      throw error
    }
  }

  const updatePost = async (id: number, params: Partial<postsApi.CreatePostParams>) => {
    try {
      const updatedPost = await postsApi.updatePost(id, params)
      const index = posts.value.findIndex(p => p.id === id)
      if (index !== -1) {
        posts.value[index] = updatedPost
      }
      if (currentPost.value?.id === id) {
        currentPost.value = updatedPost
      }
      return updatedPost
    } catch (error) {
      console.error('Failed to update post:', error)
      throw error
    }
  }

  const deletePost = async (id: number) => {
    try {
      await postsApi.deletePost(id)
      posts.value = posts.value.filter(p => p.id !== id)
      if (currentPost.value?.id === id) {
        currentPost.value = null
      }
    } catch (error) {
      console.error('Failed to delete post:', error)
      throw error
    }
  }

  /** 帖子详情与列表流可能各持有一份对象，需同时更新，否则详情页 UI 不会变 */
  const collectPostTargets = (postId: number) => {
    const set = new Set<Post>()
    const inFeed = posts.value.find(p => p.id === postId)
    const detail = currentPost.value?.id === postId ? currentPost.value : null
    if (inFeed) set.add(inFeed)
    if (detail) set.add(detail)
    return [...set]
  }

  const toggleLike = async (postId: number) => {
    const targets = collectPostTargets(postId)
    if (!targets.length) return

    const wasLiked = targets[0].isLiked

    const { like, unlike } = await import('@/api/likes')

    if (wasLiked) {
      await unlike({ targetType: 'POST', targetId: postId })
      for (const p of targets) {
        p.likes = Math.max(0, p.likes - 1)
        p.isLiked = false
      }
    } else {
      await like({ targetType: 'POST', targetId: postId })
      for (const p of targets) {
        p.likes++
        p.isLiked = true
      }
    }
  }

  const toggleFavorite = async (postId: number) => {
    const targets = collectPostTargets(postId)
    if (!targets.length) return

    const wasFavorited = targets[0].isFavorited

    if (wasFavorited) {
      await postsApi.unfavoritePost(postId)
      for (const p of targets) {
        p.isFavorited = false
      }
    } else {
      await postsApi.favoritePost(postId)
      for (const p of targets) {
        p.isFavorited = true
      }
    }
  }

  return {
    // State
    posts,
    currentPost,
    loading,
    pagination,
    
    // Actions
    fetchPosts,
    fetchPost,
    createPost,
    updatePost,
    deletePost,
    toggleLike,
    toggleFavorite
  }
})