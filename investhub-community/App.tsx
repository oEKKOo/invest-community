
import React, { useState, useMemo } from 'react';
import { User, Post, Portfolio, ContentStatus, UserRole } from './types';
import { Icons } from './constants';
import Dashboard from './modules/Dashboard';
import Community from './modules/Community';
import Portfolios from './modules/Portfolios';
import AdminModule from './modules/AdminModule';
import ProfileModule from './modules/ProfileModule';

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [isLoggedIn, setIsLoggedIn] = useState(true); // Default to true for demo
  const [currentUser] = useState<User>({
    id: 'u-1',
    username: 'investor_pro',
    displayName: 'Alex Rivers',
    avatar: 'https://picsum.photos/seed/alex/100/100',
    role: UserRole.ADMIN,
    bio: 'Long term value investor and tech enthusiast.',
    followers: 1240,
    following: 342,
  });

  const [posts, setPosts] = useState<Post[]>([
    {
      id: 'p-1',
      authorId: 'u-1',
      authorName: 'Alex Rivers',
      title: 'Why I am bullish on AI Funds in 2024',
      content: 'The generative AI revolution is just beginning. Looking at sectoral funds that focus on infrastructure...',
      status: ContentStatus.PUBLISHED,
      likes: 45,
      comments: 12,
      createdAt: '2024-05-10',
      tags: ['AI', 'Tech', 'Growth']
    },
    {
      id: 'p-2',
      authorId: 'u-2',
      authorName: 'Sara Smith',
      title: 'My Dividend Growth Strategy',
      content: 'Consistent yields are the key to long term wealth. Here is how I pick my monthly payers...',
      status: ContentStatus.PUBLISHED,
      likes: 89,
      comments: 34,
      createdAt: '2024-05-12',
      tags: ['Dividends', 'Income']
    },
    {
      id: 'p-3',
      authorId: 'u-3',
      authorName: 'Mike Johnson',
      title: 'Review: Emerging Markets Fund ABC',
      content: 'I have some concerns about the geopolitical risks in this specific regional weighting...',
      status: ContentStatus.PENDING_REVIEW,
      likes: 0,
      comments: 0,
      createdAt: '2024-05-14',
      tags: ['Review', 'EM']
    }
  ]);

  const [portfolios, setPortfolios] = useState<Portfolio[]>([
    {
      id: 'port-1',
      userId: 'u-1',
      userName: 'Alex Rivers',
      title: 'Aggressive Growth 2024',
      description: 'Focusing on high-beta tech stocks and energy transition.',
      assets: [
        { symbol: 'QQQ', name: 'Nasdaq 100', allocation: 50 },
        { symbol: 'SMH', name: 'Semiconductors', allocation: 30 },
        { symbol: 'TSLA', name: 'Tesla Inc', allocation: 20 },
      ],
      returnsYTD: 18.5,
      riskLevel: 'High',
      isPublic: true,
      likes: 56
    }
  ]);

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <Dashboard posts={posts.filter(p => p.status === ContentStatus.PUBLISHED)} portfolios={portfolios} />;
      case 'community':
        return <Community posts={posts} setPosts={setPosts} currentUser={currentUser} />;
      case 'portfolios':
        return <Portfolios portfolios={portfolios} setPortfolios={setPortfolios} currentUser={currentUser} />;
      case 'admin':
        return currentUser.role !== UserRole.USER ? (
          <AdminModule posts={posts} setPosts={setPosts} />
        ) : (
          <div className="p-8 text-center text-gray-500">Access Denied</div>
        );
      case 'profile':
        return <ProfileModule user={currentUser} userPosts={posts.filter(p => p.authorId === currentUser.id)} />;
      default:
        return <Dashboard posts={posts} portfolios={portfolios} />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col md:flex-row">
      {/* Sidebar - Navigation */}
      <aside className="w-full md:w-64 bg-white border-r border-gray-200 sticky top-0 h-auto md:h-screen z-20 overflow-y-auto">
        <div className="p-6 flex items-center gap-2">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center text-white font-bold">IH</div>
          <h1 className="text-xl font-bold text-gray-800">InvestHub</h1>
        </div>

        <nav className="mt-4 px-4 space-y-1">
          <button 
            onClick={() => setActiveTab('dashboard')}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${activeTab === 'dashboard' ? 'bg-blue-50 text-blue-600' : 'text-gray-600 hover:bg-gray-100'}`}
          >
            <Icons.Home />
            <span className="font-medium">Dashboard</span>
          </button>
          <button 
            onClick={() => setActiveTab('community')}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${activeTab === 'community' ? 'bg-blue-50 text-blue-600' : 'text-gray-600 hover:bg-gray-100'}`}
          >
            <Icons.Community />
            <span className="font-medium">Community</span>
          </button>
          <button 
            onClick={() => setActiveTab('portfolios')}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${activeTab === 'portfolios' ? 'bg-blue-50 text-blue-600' : 'text-gray-600 hover:bg-gray-100'}`}
          >
            <Icons.Portfolio />
            <span className="font-medium">Portfolios</span>
          </button>
          {currentUser.role !== UserRole.USER && (
            <button 
              onClick={() => setActiveTab('admin')}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${activeTab === 'admin' ? 'bg-blue-50 text-blue-600' : 'text-gray-600 hover:bg-gray-100'}`}
            >
              <Icons.Admin />
              <span className="font-medium">Admin Panel</span>
            </button>
          )}
          <button 
            onClick={() => setActiveTab('profile')}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${activeTab === 'profile' ? 'bg-blue-50 text-blue-600' : 'text-gray-600 hover:bg-gray-100'}`}
          >
            <Icons.Profile />
            <span className="font-medium">My Profile</span>
          </button>
        </nav>

        <div className="absolute bottom-0 w-full p-4 border-t border-gray-100 bg-white hidden md:block">
          {isLoggedIn ? (
            <div className="flex items-center gap-3 px-2 py-3">
              <img src={currentUser.avatar} alt="avatar" className="w-10 h-10 rounded-full border border-gray-200" />
              <div className="flex-1 overflow-hidden">
                <p className="text-sm font-semibold truncate">{currentUser.displayName}</p>
                <p className="text-xs text-gray-500">@{currentUser.username}</p>
              </div>
              <button onClick={() => setIsLoggedIn(false)} className="text-gray-400 hover:text-red-500">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" x2="9" y1="12" y2="12"/></svg>
              </button>
            </div>
          ) : (
            <button onClick={() => setIsLoggedIn(true)} className="w-full bg-blue-600 text-white py-2 rounded-lg font-medium">Log In</button>
          )}
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 overflow-y-auto">
        <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6 sticky top-0 z-10">
          <div className="relative w-full max-w-md">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
              <Icons.Search />
            </span>
            <input 
              type="text" 
              placeholder="Search discussions, funds, portfolios..." 
              className="w-full pl-10 pr-4 py-2 bg-gray-100 border-none rounded-lg focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all text-sm"
            />
          </div>
          <div className="flex items-center gap-4">
            <button className="p-2 text-gray-500 hover:bg-gray-100 rounded-full relative">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/></svg>
              <span className="absolute top-2 right-2 w-2 h-2 bg-red-500 border-2 border-white rounded-full"></span>
            </button>
          </div>
        </header>

        <div className="p-6">
          {renderContent()}
        </div>
      </main>
    </div>
  );
};

export default App;
