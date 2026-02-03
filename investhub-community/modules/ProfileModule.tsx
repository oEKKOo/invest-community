
import React from 'react';
import { User, Post } from '../types';
import { Icons } from '../constants';

interface ProfileModuleProps {
  user: User;
  userPosts: Post[];
}

const ProfileModule: React.FC<ProfileModuleProps> = ({ user, userPosts }) => {
  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header Profile Section */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-8 flex flex-col items-center md:flex-row md:items-start gap-8">
        <img src={user.avatar} className="w-32 h-32 rounded-3xl border-4 border-white shadow-lg" />
        <div className="flex-1 text-center md:text-left">
          <div className="flex flex-col md:flex-row md:items-center gap-4 mb-2">
            <h2 className="text-3xl font-black">{user.displayName}</h2>
            <span className="bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-widest">{user.role}</span>
          </div>
          <p className="text-gray-500 font-medium mb-4">@{user.username}</p>
          <p className="text-gray-600 leading-relaxed mb-6 max-w-xl">{user.bio}</p>
          <div className="flex items-center justify-center md:justify-start gap-8">
            <div className="text-center">
              <p className="text-xl font-black">{user.followers}</p>
              <p className="text-xs text-gray-400 uppercase font-bold tracking-widest">Followers</p>
            </div>
            <div className="text-center">
              <p className="text-xl font-black">{user.following}</p>
              <p className="text-xs text-gray-400 uppercase font-bold tracking-widest">Following</p>
            </div>
            <div className="text-center">
              <p className="text-xl font-black">{userPosts.length}</p>
              <p className="text-xs text-gray-400 uppercase font-bold tracking-widest">Posts</p>
            </div>
          </div>
        </div>
        <div className="flex gap-2">
          <button className="bg-gray-100 text-gray-800 px-6 py-2 rounded-xl font-bold hover:bg-gray-200">Edit Profile</button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {/* Left: Security/Account Module */}
        <aside className="space-y-6">
          <div className="bg-white p-6 rounded-2xl border border-gray-100 shadow-sm">
            <h3 className="font-bold mb-4">Account & Security</h3>
            <ul className="space-y-3">
              <li className="flex items-center justify-between text-sm">
                <span className="text-gray-500">Email Verification</span>
                <span className="text-green-600 font-bold">Verified</span>
              </li>
              <li className="flex items-center justify-between text-sm">
                <span className="text-gray-500">Two-Factor Auth</span>
                <button className="text-blue-600 hover:underline">Enable</button>
              </li>
              <li className="flex items-center justify-between text-sm">
                <span className="text-gray-500">Account Type</span>
                <span className="text-gray-800 font-bold">Professional</span>
              </li>
            </ul>
          </div>

          <div className="bg-blue-600 text-white p-6 rounded-2xl shadow-lg shadow-blue-100">
            <h4 className="font-bold mb-2">Invite Friends</h4>
            <p className="text-xs opacity-80 mb-4">Get 3 months of premium analytics for every successful referral.</p>
            <button className="w-full bg-white text-blue-600 py-2 rounded-lg font-bold text-sm">Copy Link</button>
          </div>
        </aside>

        {/* Right: Personal Activity */}
        <div className="md:col-span-2 space-y-4">
          <h3 className="text-xl font-bold px-2">Recent Activity</h3>
          {userPosts.map(post => (
            <div key={post.id} className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between mb-2">
                <span className={`text-[10px] px-2 py-0.5 rounded font-bold tracking-wider uppercase ${
                  post.status === 'PUBLISHED' ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'
                }`}>
                  {post.status}
                </span>
                <span className="text-[10px] text-gray-400 font-bold">{post.createdAt}</span>
              </div>
              <h4 className="font-bold text-gray-800 mb-1">{post.title}</h4>
              <p className="text-sm text-gray-500 line-clamp-1">{post.content}</p>
              <div className="flex gap-4 mt-3">
                <span className="flex items-center gap-1 text-xs text-gray-400"><Icons.Heart /> {post.likes}</span>
                <span className="flex items-center gap-1 text-xs text-gray-400"><Icons.Message /> {post.comments}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ProfileModule;
