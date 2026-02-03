
import React from 'react';
import { Post, Portfolio } from '../types';
import { Icons } from '../constants';
import { LineChart, Line, ResponsiveContainer, XAxis, YAxis, Tooltip } from 'recharts';

interface DashboardProps {
  posts: Post[];
  portfolios: Portfolio[];
}

const mockMarketData = [
  { name: 'Mon', value: 4200 },
  { name: 'Tue', value: 4350 },
  { name: 'Wed', value: 4100 },
  { name: 'Thu', value: 4450 },
  { name: 'Fri', value: 4600 },
];

const Dashboard: React.FC<DashboardProps> = ({ posts, portfolios }) => {
  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Hero Section / Market Overview */}
      <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
          <div className="flex justify-between items-center mb-6">
            <div>
              <h2 className="text-lg font-bold">Market Sentiment</h2>
              <p className="text-sm text-gray-500">S&P 500 Index Overview</p>
            </div>
            <div className="flex items-center gap-2 text-green-600 font-bold">
              <span>+2.4%</span>
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg>
            </div>
          </div>
          <div className="h-48 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={mockMarketData}>
                <Line type="monotone" dataKey="value" stroke="#2563eb" strokeWidth={3} dot={false} />
                <XAxis dataKey="name" hide />
                <YAxis hide domain={['auto', 'auto']} />
                <Tooltip />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
        
        <div className="bg-blue-600 rounded-2xl p-6 text-white flex flex-col justify-between shadow-lg shadow-blue-100">
          <div>
            <h3 className="text-xl font-bold mb-2">Build Your Legacy</h3>
            <p className="text-blue-100 text-sm opacity-90">Share your investment strategies and grow with the community.</p>
          </div>
          <button className="mt-4 bg-white text-blue-600 px-4 py-2 rounded-lg font-semibold text-sm self-start hover:bg-blue-50 transition-colors">
            Create Portfolio
          </button>
        </div>
      </section>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Recent Posts */}
        <section className="lg:col-span-2 space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-bold">Trending Discussions</h2>
            <button className="text-blue-600 text-sm font-semibold">View All</button>
          </div>
          <div className="space-y-4">
            {posts.map(post => (
              <div key={post.id} className="bg-white p-5 rounded-xl border border-gray-100 shadow-sm hover:shadow-md transition-shadow">
                <div className="flex gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-xs font-bold text-blue-600 uppercase tracking-wider">{post.tags[0]}</span>
                      <span className="text-xs text-gray-400">•</span>
                      <span className="text-xs text-gray-500">{post.createdAt}</span>
                    </div>
                    <h3 className="font-bold text-lg mb-2 hover:text-blue-600 cursor-pointer">{post.title}</h3>
                    <p className="text-gray-600 text-sm line-clamp-2">{post.content}</p>
                    <div className="flex items-center gap-6 mt-4">
                      <button className="flex items-center gap-1.5 text-gray-500 hover:text-red-500 text-sm transition-colors">
                        <Icons.Heart /> <span>{post.likes}</span>
                      </button>
                      <button className="flex items-center gap-1.5 text-gray-500 hover:text-blue-500 text-sm transition-colors">
                        <Icons.Message /> <span>{post.comments}</span>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Top Portfolios Sidebar */}
        <section className="space-y-4">
          <h2 className="text-xl font-bold">Top Performing Portfolios</h2>
          <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
            {portfolios.map((port, idx) => (
              <div key={port.id} className={`p-4 hover:bg-gray-50 cursor-pointer transition-colors ${idx !== portfolios.length - 1 ? 'border-b border-gray-100' : ''}`}>
                <div className="flex items-center justify-between mb-2">
                  <p className="text-sm font-bold truncate pr-4">{port.title}</p>
                  <span className={`text-xs px-2 py-0.5 rounded-full font-bold ${port.returnsYTD >= 0 ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                    +{port.returnsYTD}%
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <img src={`https://picsum.photos/seed/${port.id}/32/32`} className="w-6 h-6 rounded-full" />
                  <p className="text-xs text-gray-500">by {port.userName}</p>
                </div>
              </div>
            ))}
            <div className="p-4 bg-gray-50 text-center">
              <button className="text-sm font-semibold text-gray-600 hover:text-blue-600">Browse Leaderboard</button>
            </div>
          </div>

          <div className="bg-gradient-to-br from-indigo-500 to-purple-600 p-6 rounded-2xl text-white shadow-lg">
            <p className="text-xs font-bold uppercase tracking-widest mb-2 opacity-80">Community Stats</p>
            <div className="flex items-center justify-between">
              <div>
                <h4 className="text-2xl font-bold">12.4k</h4>
                <p className="text-xs opacity-70">Active Investors</p>
              </div>
              <div>
                <h4 className="text-2xl font-bold">342</h4>
                <p className="text-xs opacity-70">Strategies Shared</p>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
};

export default Dashboard;
