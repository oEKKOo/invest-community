
import React, { useState } from 'react';
import { Post, User, ContentStatus } from '../types';
import { Icons } from '../constants';

interface CommunityProps {
  posts: Post[];
  setPosts: React.Dispatch<React.SetStateAction<Post[]>>;
  currentUser: User;
}

const Community: React.FC<CommunityProps> = ({ posts, setPosts, currentUser }) => {
  const [isCreating, setIsCreating] = useState(false);
  const [newPost, setNewPost] = useState({ title: '', content: '', tags: '' });
  const [activeFilter, setActiveFilter] = useState<ContentStatus | 'ALL'>('ALL');

  const handleCreatePost = (status: ContentStatus) => {
    if (!newPost.title || !newPost.content) return;

    const post: Post = {
      id: `p-${Date.now()}`,
      authorId: currentUser.id,
      authorName: currentUser.displayName,
      title: newPost.title,
      content: newPost.content,
      status: status,
      likes: 0,
      comments: 0,
      createdAt: new Date().toISOString().split('T')[0],
      tags: newPost.tags.split(',').map(t => t.trim()).filter(t => t)
    };

    setPosts(prev => [post, ...prev]);
    setIsCreating(false);
    setNewPost({ title: '', content: '', tags: '' });
  };

  const filteredPosts = posts.filter(p => 
    (activeFilter === 'ALL' ? (p.status === ContentStatus.PUBLISHED || p.authorId === currentUser.id) : p.status === activeFilter)
  );

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Community Forum</h2>
        <button 
          onClick={() => setIsCreating(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg font-semibold flex items-center gap-2 shadow-lg shadow-blue-100 hover:bg-blue-700 transition-colors"
        >
          <Icons.Plus /> New Discussion
        </button>
      </div>

      <div className="flex gap-2 border-b border-gray-200">
        {(['ALL', ContentStatus.PUBLISHED, ContentStatus.PENDING_REVIEW, ContentStatus.DRAFT] as const).map(status => (
          <button
            key={status}
            onClick={() => setActiveFilter(status)}
            className={`px-4 py-3 text-sm font-medium transition-colors border-b-2 ${activeFilter === status ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
          >
            {status.replace('_', ' ')}
          </button>
        ))}
      </div>

      {isCreating && (
        <div className="bg-white p-6 rounded-2xl shadow-xl border border-blue-100 animate-slideUp">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-bold">Share your thoughts</h3>
            <button onClick={() => setIsCreating(false)} className="text-gray-400 hover:text-gray-600"><Icons.X /></button>
          </div>
          <div className="space-y-4">
            <input 
              type="text" 
              placeholder="Give your discussion a title..."
              className="w-full text-xl font-bold border-none bg-gray-50 rounded-lg focus:ring-0 px-4 py-2"
              value={newPost.title}
              onChange={e => setNewPost({...newPost, title: e.target.value})}
            />
            <textarea 
              rows={6}
              placeholder="What would you like to discuss today? Analyses, news, or questions..."
              className="w-full border-none bg-gray-50 rounded-lg focus:ring-0 p-4 resize-none"
              value={newPost.content}
              onChange={e => setNewPost({...newPost, content: e.target.value})}
            />
            <input 
              type="text" 
              placeholder="Tags (comma separated)... e.g. S&P500, Dividend, ETF"
              className="w-full text-sm border-none bg-gray-50 rounded-lg focus:ring-0 px-4 py-2"
              value={newPost.tags}
              onChange={e => setNewPost({...newPost, tags: e.target.value})}
            />
            <div className="flex justify-end gap-3 pt-4">
              <button 
                onClick={() => handleCreatePost(ContentStatus.DRAFT)}
                className="px-6 py-2 text-gray-600 font-semibold hover:bg-gray-100 rounded-lg"
              >
                Save Draft
              </button>
              <button 
                onClick={() => handleCreatePost(ContentStatus.PENDING_REVIEW)}
                className="bg-blue-600 text-white px-8 py-2 rounded-lg font-bold shadow-md shadow-blue-100 hover:bg-blue-700"
              >
                Submit for Review
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="space-y-4">
        {filteredPosts.length === 0 ? (
          <div className="p-20 text-center bg-white rounded-2xl border border-dashed border-gray-300">
            <p className="text-gray-500 font-medium">No posts found in this category.</p>
          </div>
        ) : (
          filteredPosts.map(post => (
            <div key={post.id} className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 group">
              <div className="flex justify-between items-start mb-4">
                <div className="flex items-center gap-3">
                  <img src={`https://picsum.photos/seed/${post.authorId}/40/40`} className="w-10 h-10 rounded-full" />
                  <div>
                    <p className="text-sm font-bold">{post.authorName}</p>
                    <p className="text-xs text-gray-500">{post.createdAt}</p>
                  </div>
                </div>
                <div className={`text-xs px-2 py-1 rounded-md font-bold ${
                  post.status === ContentStatus.PUBLISHED ? 'bg-green-100 text-green-700' :
                  post.status === ContentStatus.PENDING_REVIEW ? 'bg-amber-100 text-amber-700' :
                  'bg-gray-100 text-gray-700'
                }`}>
                  {post.status.replace('_', ' ')}
                </div>
              </div>
              <h3 className="text-xl font-bold mb-3 group-hover:text-blue-600 transition-colors cursor-pointer">{post.title}</h3>
              <p className="text-gray-600 leading-relaxed mb-4">{post.content}</p>
              <div className="flex flex-wrap gap-2 mb-6">
                {post.tags.map(tag => (
                  <span key={tag} className="px-2 py-1 bg-gray-100 text-gray-500 rounded text-xs font-medium">#{tag}</span>
                ))}
              </div>
              <div className="flex items-center gap-6 border-t border-gray-50 pt-4">
                <button className="flex items-center gap-2 text-gray-500 hover:text-red-500 transition-colors">
                  <Icons.Heart /> <span className="font-medium">{post.likes}</span>
                </button>
                <button className="flex items-center gap-2 text-gray-500 hover:text-blue-600 transition-colors">
                  <Icons.Message /> <span className="font-medium">{post.comments}</span>
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default Community;
