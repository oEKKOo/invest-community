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

  const toggleLike = async (postId: number) => {
    const post = posts.value.find(p => p.id === postId) || currentPost.value
    if (!post) return

    const wasLiked = post.isLiked
    
    try {
      // 动态导入避免循环依赖
      const { like, unlike } = await import('@/api/likes')
      
      if (wasLiked) {
        await unlike({ targetType: 'POST', targetId: postId })
        post.likes--
        post.isLiked = false
      } else {
        await like({ targetType: 'POST', targetId: postId })
        post.likes++
        post.isLiked = true
      }
    } catch (error) {
      // 回滚状态
      post.isLiked = wasLiked
      post.likes += wasLiked ? 1 : -1
      throw error
    }
  }

  const toggleFavorite = async (postId: number) => {
    const post = posts.value.find(p => p.id === postId) || currentPost.value
    if (!post) return

    const wasFavorited = post.isFavorited

    try {
      if (wasFavorited) {
        await postsApi.unfavoritePost(postId)
        post.isFavorited = false
      } else {
        await postsApi.favoritePost(postId)
        post.isFavorited = true
      }
    } catch (error) {
      // 回滚状态
      post.isFavorited = wasFavorited
      throw error
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