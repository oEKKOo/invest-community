import { post, del } from './index'

// 点赞
export interface LikeParams {
  targetType: 'POST' | 'COMMENT' | 'PORTFOLIO'
  targetId: number
}

export const like = (params: LikeParams): Promise<void> => {
  return post('/likes/', params)
}

// 取消点赞
export const unlike = (params: LikeParams): Promise<void> => {
  return del('/likes/', { data: params })
}