
import React, { useState } from 'react';
import { Portfolio, User, PortfolioAsset } from '../types';
import { Icons } from '../constants';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';

interface PortfoliosProps {
  portfolios: Portfolio[];
  setPortfolios: React.Dispatch<React.SetStateAction<Portfolio[]>>;
  currentUser: User;
}

const COLORS = ['#2563eb', '#7c3aed', '#db2777', '#ea580c', '#16a34a', '#4b5563'];

const Portfolios: React.FC<PortfoliosProps> = ({ portfolios, setPortfolios, currentUser }) => {
  const [isCreating, setIsCreating] = useState(false);
  const [newPortfolio, setNewPortfolio] = useState({
    title: '',
    description: '',
    riskLevel: 'Medium' as 'Low' | 'Medium' | 'High',
    assets: [] as PortfolioAsset[]
  });
  const [assetForm, setAssetForm] = useState({ symbol: '', name: '', allocation: 0 });

  const addAsset = () => {
    if (!assetForm.symbol || !assetForm.allocation) return;
    setNewPortfolio({
      ...newPortfolio,
      assets: [...newPortfolio.assets, { ...assetForm }]
    });
    setAssetForm({ symbol: '', name: '', allocation: 0 });
  };

  const handleSave = () => {
    const portfolio: Portfolio = {
      id: `port-${Date.now()}`,
      userId: currentUser.id,
      userName: currentUser.displayName,
      title: newPortfolio.title,
      description: newPortfolio.description,
      assets: newPortfolio.assets,
      returnsYTD: 0,
      riskLevel: newPortfolio.riskLevel,
      isPublic: true,
      likes: 0
    };
    setPortfolios([portfolio, ...portfolios]);
    setIsCreating(false);
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Investment Portfolios</h2>
        <button 
          onClick={() => setIsCreating(true)}
          className="bg-indigo-600 text-white px-4 py-2 rounded-lg font-semibold flex items-center gap-2 hover:bg-indigo-700"
        >
          <Icons.Plus /> Create My Portfolio
        </button>
      </div>

      {isCreating && (
        <div className="bg-white p-8 rounded-2xl border-2 border-indigo-100 shadow-xl space-y-6 animate-fadeIn">
          <div className="flex justify-between">
            <h3 className="text-xl font-bold">Build Strategy</h3>
            <button onClick={() => setIsCreating(false)}><Icons.X /></button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <input 
                type="text" placeholder="Portfolio Name" 
                className="w-full px-4 py-2 bg-gray-50 border-none rounded-lg"
                value={newPortfolio.title} onChange={e => setNewPortfolio({...newPortfolio, title: e.target.value})}
              />
              <textarea 
                placeholder="Describe your strategy..."
                className="w-full px-4 py-2 bg-gray-50 border-none rounded-lg h-24"
                value={newPortfolio.description} onChange={e => setNewPortfolio({...newPortfolio, description: e.target.value})}
              />
              <select 
                className="w-full px-4 py-2 bg-gray-50 border-none rounded-lg"
                value={newPortfolio.riskLevel} onChange={e => setNewPortfolio({...newPortfolio, riskLevel: e.target.value as any})}
              >
                <option value="Low">Low Risk</option>
                <option value="Medium">Medium Risk</option>
                <option value="High">High Risk</option>
              </select>
            </div>
            
            <div className="bg-gray-50 p-4 rounded-xl space-y-3">
              <p className="font-bold text-sm uppercase text-gray-500">Add Assets</p>
              <div className="flex gap-2">
                <input 
                  type="text" placeholder="Symbol" className="w-24 bg-white px-3 py-1.5 rounded border-none"
                  value={assetForm.symbol} onChange={e => setAssetForm({...assetForm, symbol: e.target.value.toUpperCase()})}
                />
                <input 
                  type="number" placeholder="%" className="w-16 bg-white px-3 py-1.5 rounded border-none"
                  value={assetForm.allocation || ''} onChange={e => setAssetForm({...assetForm, allocation: Number(e.target.value)})}
                />
                <button onClick={addAsset} className="bg-gray-800 text-white px-3 py-1.5 rounded hover:bg-black transition-colors">Add</button>
              </div>
              <div className="space-y-2 mt-4 max-h-32 overflow-y-auto">
                {newPortfolio.assets.map((asset, i) => (
                  <div key={i} className="flex justify-between items-center text-sm p-2 bg-white rounded shadow-sm">
                    <span className="font-bold">{asset.symbol}</span>
                    <span className="text-indigo-600 font-bold">{asset.allocation}%</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
          <div className="flex justify-end pt-4">
            <button 
              onClick={handleSave}
              className="bg-indigo-600 text-white px-8 py-2 rounded-lg font-bold hover:bg-indigo-700 shadow-lg shadow-indigo-100"
            >
              Publish Portfolio
            </button>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
        {portfolios.map(port => (
          <div key={port.id} className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden hover:shadow-lg transition-all flex flex-col">
            <div className="p-6 flex-1">
              <div className="flex justify-between items-start mb-4">
                <h3 className="text-lg font-bold">{port.title}</h3>
                <span className={`text-xs px-2 py-1 rounded-full font-bold ${
                  port.riskLevel === 'High' ? 'bg-red-50 text-red-600' : 
                  port.riskLevel === 'Medium' ? 'bg-amber-50 text-amber-600' : 'bg-green-50 text-green-600'
                }`}>
                  {port.riskLevel} Risk
                </span>
              </div>
              <p className="text-gray-500 text-sm mb-4 line-clamp-2 h-10">{port.description}</p>
              
              <div className="h-40 w-full mb-4">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={port.assets}
                      dataKey="allocation"
                      nameKey="symbol"
                      innerRadius={40}
                      outerRadius={60}
                      paddingAngle={5}
                    >
                      {port.assets.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>

              <div className="flex items-center justify-between text-xs font-bold text-gray-400 uppercase tracking-widest">
                <span>Top Allocation</span>
                <span>YTD Return</span>
              </div>
              <div className="flex items-center justify-between mt-1">
                <span className="text-sm font-bold">{port.assets[0]?.symbol || 'N/A'}</span>
                <span className="text-sm font-bold text-green-600">+{port.returnsYTD}%</span>
              </div>
            </div>
            <div className="p-4 bg-gray-50 border-t border-gray-100 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <img src={`https://picsum.photos/seed/${port.id}/30/30`} className="w-8 h-8 rounded-full" />
                <span className="text-sm font-medium text-gray-700">{port.userName}</span>
              </div>
              <button className="flex items-center gap-1.5 text-gray-400 hover:text-red-500 transition-colors">
                <Icons.Heart /> <span className="text-sm">{port.likes}</span>
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Portfolios;
