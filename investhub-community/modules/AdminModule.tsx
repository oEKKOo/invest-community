
import React from 'react';
import { Post, ContentStatus } from '../types';
import { Icons } from '../constants';

interface AdminModuleProps {
  posts: Post[];
  setPosts: React.Dispatch<React.SetStateAction<Post[]>>;
}

const AdminModule: React.FC<AdminModuleProps> = ({ posts, setPosts }) => {
  const pendingPosts = posts.filter(p => p.status === ContentStatus.PENDING_REVIEW);

  const handleStatusChange = (postId: string, newStatus: ContentStatus) => {
    setPosts(prev => prev.map(p => p.id === postId ? { ...p, status: newStatus } : p));
  };

  return (
    <div className="space-y-8">
      <div className="flex items-center gap-4 mb-8">
        <div className="p-3 bg-red-100 text-red-600 rounded-xl">
          <Icons.Admin />
        </div>
        <div>
          <h2 className="text-2xl font-bold">Admin Dashboard</h2>
          <p className="text-gray-500">Moderation and community governance center</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm">
          <p className="text-sm font-bold text-gray-400 uppercase tracking-widest mb-1">Pending Approval</p>
          <p className="text-3xl font-black text-amber-600">{pendingPosts.length}</p>
        </div>
        <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm">
          <p className="text-sm font-bold text-gray-400 uppercase tracking-widest mb-1">Open Reports</p>
          <p className="text-3xl font-black text-red-600">3</p>
        </div>
        <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm">
          <p className="text-sm font-bold text-gray-400 uppercase tracking-widest mb-1">New Users (24h)</p>
          <p className="text-3xl font-black text-blue-600">42</p>
        </div>
      </div>

      <section className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="p-6 border-b border-gray-100">
          <h3 className="font-bold text-lg">Content Moderation Queue</h3>
          <p className="text-sm text-gray-500">Review pending posts before they go live</p>
        </div>
        
        <div className="divide-y divide-gray-100">
          {pendingPosts.length === 0 ? (
            <div className="p-20 text-center text-gray-500">
              <div className="w-16 h-16 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-4">
                <Icons.Check />
              </div>
              <p>Great job! The queue is empty.</p>
            </div>
          ) : (
            pendingPosts.map(post => (
              <div key={post.id} className="p-6 hover:bg-gray-50 transition-colors">
                <div className="flex flex-col lg:flex-row gap-6">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-3">
                      <img src={`https://picsum.photos/seed/${post.authorId}/32/32`} className="w-6 h-6 rounded-full" />
                      <span className="text-sm font-bold">{post.authorName}</span>
                      <span className="text-gray-300">•</span>
                      <span className="text-xs text-gray-500">{post.createdAt}</span>
                    </div>
                    <h4 className="font-bold text-lg mb-2">{post.title}</h4>
                    <p className="text-gray-600 text-sm mb-4">{post.content}</p>
                    <div className="flex gap-2">
                      {post.tags.map(t => <span key={t} className="px-2 py-0.5 bg-gray-100 text-gray-500 text-xs rounded">#{t}</span>)}
                    </div>
                  </div>
                  <div className="flex lg:flex-col gap-3 justify-center">
                    <button 
                      onClick={() => handleStatusChange(post.id, ContentStatus.PUBLISHED)}
                      className="flex items-center justify-center gap-2 bg-green-600 text-white px-4 py-2 rounded-lg font-bold hover:bg-green-700"
                    >
                      <Icons.Check /> Approve
                    </button>
                    <button 
                      onClick={() => handleStatusChange(post.id, ContentStatus.REJECTED)}
                      className="flex items-center justify-center gap-2 bg-red-50 text-red-600 px-4 py-2 rounded-lg font-bold border border-red-100 hover:bg-red-100"
                    >
                      <Icons.X /> Reject
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </section>

      <section className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
        <h3 className="font-bold text-lg mb-4">Recent Community Alerts</h3>
        <div className="space-y-4">
          {[1, 2].map(i => (
            <div key={i} className="flex items-start gap-4 p-4 bg-red-50 rounded-xl border border-red-100">
              <div className="w-8 h-8 bg-red-200 text-red-700 rounded-full flex items-center justify-center flex-shrink-0">
                !
              </div>
              <div className="flex-1">
                <p className="text-sm font-bold text-red-800">Potential Misinformation Flagged</p>
                <p className="text-xs text-red-600 mt-1">AI detected high probability of unverified financial advice in thread #492.</p>
                <div className="flex gap-4 mt-3">
                  <button className="text-xs font-bold text-red-700 hover:underline">View Source</button>
                  <button className="text-xs font-bold text-red-700 hover:underline">Dismiss</button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
};

export default AdminModule;
