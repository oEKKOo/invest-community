
export enum ContentStatus {
  DRAFT = 'DRAFT',
  PENDING_REVIEW = 'PENDING_REVIEW',
  PUBLISHED = 'PUBLISHED',
  REJECTED = 'REJECTED',
  TAKEN_DOWN = 'TAKEN_DOWN'
}

export enum UserRole {
  USER = 'USER',
  MODERATOR = 'MODERATOR',
  ADMIN = 'ADMIN'
}

export interface User {
  id: string;
  username: string;
  displayName: string;
  avatar: string;
  role: UserRole;
  bio?: string;
  followers: number;
  following: number;
}

export interface Post {
  id: string;
  authorId: string;
  authorName: string;
  title: string;
  content: string;
  status: ContentStatus;
  likes: number;
  comments: number;
  createdAt: string;
  tags: string[];
}

export interface PortfolioAsset {
  symbol: string;
  name: string;
  allocation: number; // percentage
}

export interface Portfolio {
  id: string;
  userId: string;
  userName: string;
  title: string;
  description: string;
  assets: PortfolioAsset[];
  returnsYTD: number;
  riskLevel: 'Low' | 'Medium' | 'High';
  isPublic: boolean;
  likes: number;
}

export interface Comment {
  id: string;
  postId: string;
  authorId: string;
  authorName: string;
  authorAvatar: string;
  text: string;
  createdAt: string;
}

export interface Report {
  id: string;
  targetType: 'POST' | 'COMMENT' | 'USER';
  targetId: string;
  reason: string;
  reporterId: string;
  status: 'PENDING' | 'RESOLVED';
  createdAt: string;
}
