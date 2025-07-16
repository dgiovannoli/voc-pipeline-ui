import React, { useState } from 'react';

const WinLossDashboard = () => {
  const [currentPage, setCurrentPage] = useState('dashboard');
  const [searchQuery, setSearchQuery] = useState('');
  const [industryFilter, setIndustryFilter] = useState('all');
  const [feedFilter, setFeedFilter] = useState('all');
  const [timeFilter, setTimeFilter] = useState('7days');
  const [expandedView, setExpandedView] = useState(null);
  
  // Sample quotes data with timestamps
  const quotes = [
    {
      id: 1,
      customerName: 'TechFlow Inc',
      dealSize: '$850K',
      outcome: 'loss',
      industry: 'Technology',
      quote: "The pricing just didn't make sense for our budget. CloudSync was 40% cheaper.",
      themes: ['#pricing-concerns', '#competitor-comparison'],
      followUpStatus: 'pending',
      timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000), // 2 hours ago
      interviewer: 'Sarah Johnson',
      tags: ['pricing', 'competitor', 'budget']
    },
    {
      id: 2,
      customerName: 'Glamour Beauty Co',
      dealSize: '$420K',
      outcome: 'win',
      industry: 'Health & Beauty',
      quote: "Your analytics dashboard is exactly what we needed for skincare tracking.",
      themes: ['#product-strength', '#analytics-advantage'],
      followUpStatus: 'completed',
      timestamp: new Date(Date.now() - 5 * 60 * 60 * 1000), // 5 hours ago
      interviewer: 'Mike Chen',
      tags: ['analytics', 'reporting', 'efficiency']
    },
    {
      id: 3,
      customerName: 'Farm Fresh Foods',
      dealSize: '$1.2M',
      outcome: 'loss',
      industry: 'Food & Beverage',
      quote: "Implementation timeline was too long for our seasonal schedule.",
      themes: ['#implementation-speed', '#seasonal-constraints'],
      followUpStatus: 'pending',
      timestamp: new Date(Date.now() - 8 * 60 * 60 * 1000), // 8 hours ago
      interviewer: 'Lisa Park',
      tags: ['timeline', 'implementation', 'urgency']
    },
    {
      id: 4,
      customerName: 'StyleCorp Fashion',
      dealSize: '$675K',
      outcome: 'win',
      industry: 'Apparel',
      quote: "Your sales team really understood our fast fashion business model.",
      themes: ['#sales-excellence', '#industry-expertise'],
      followUpStatus: 'completed',
      timestamp: new Date(Date.now() - 12 * 60 * 60 * 1000), // 12 hours ago
      interviewer: 'Tom Wilson',
      tags: ['partnership', 'demo', 'relationship']
    }
  ];
  
  // Sample factors data for dashboard
  const factors = [
    { name: 'Sales Experience & Partnership', color: '#7c3aed', trend: 'declining', arrImpact: 982000, customers: ['InnovateCorp', 'MetaScale', 'CloudVision'] },
    { name: 'Commercial Terms', color: '#0ea5e9', trend: 'declining', arrImpact: 814000, customers: ['CloudVision', 'DataSync Ltd', 'VelocityTech'] },
    { name: 'Speed & Responsiveness', color: '#06b6d4', trend: 'declining', arrImpact: 398000, customers: ['SmartBridge', 'Acme Corp', 'FlexiTech'] },
    { name: 'Product Capability', color: '#f59e0b', trend: 'improving', arrImpact: 780000, customers: ['TechFlow Inc', 'NexGen Systems', 'Acme Corp'] }
  ];
  
  const generateTimeSeriesData = () => {
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'];
    return months.map((month, index) => ({
      month,
      'Commercial Terms': [48, 48, 52, 59, 33, 26][index],
      'Sales Experience & Partnership': [45, 47, 50, 55, 40, 35][index],
      'Product Capability': [60, 65, 70, 75, 78, 80][index],
      'Speed & Responsiveness': [55, 58, 60, 58, 52, 48][index]
    }));
  };
  
  const industries = ['Technology', 'Health & Beauty', 'Food & Beverage', 'Apparel'];
  const themes = ['#pricing-concerns', '#competitor-comparison', '#product-strength', '#implementation-speed'];
  
  const formatARR = (amount) => {
    if (amount >= 1000000) return `${(amount / 1000000).toFixed(1)}M`;
    if (amount >= 1000) return `${(amount / 1000).toFixed(0)}K`;
    return `${amount}`;
  };
  
  const formatTimeAgo = (timestamp) => {
    const now = new Date();
    const diff = now - timestamp;
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    
    if (days > 0) return `${days} day${days > 1 ? 's' : ''} ago`;
    if (hours > 0) return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    return 'Just now';
  };
  
  const getNewsfeedQuotes = () => {
    let filtered = quotes;
    
    if (feedFilter === 'wins') {
      filtered = filtered.filter(q => q.outcome === 'win');
    } else if (feedFilter === 'losses') {
      filtered = filtered.filter(q => q.outcome === 'loss');
    }
    
    const now = new Date();
    const cutoff = timeFilter === '7days' ? 7 : 30;
    const timeLimit = new Date(now - cutoff * 24 * 60 * 60 * 1000);
    filtered = filtered.filter(q => q.timestamp > timeLimit);
    
    return filtered.sort((a, b) => b.timestamp - a.timestamp);
  };
  
  const getFilteredQuotes = () => {
    let filtered = quotes;
    
    if (industryFilter !== 'all') {
      filtered = filtered.filter(q => q.industry === industryFilter);
    }
    
    if (searchQuery) {
      filtered = filtered.filter(q => 
        q.quote.toLowerCase().includes(searchQuery.toLowerCase()) ||
        q.customerName.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }
    
    return filtered;
  };
  
  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h1 className="text-4xl font-bold text-gray-900">
              {currentPage === 'dashboard' ? 'Win-Loss Analysis' : 
               currentPage === 'newsfeed' ? 'Latest Insights' : 'Research Hub'}
            </h1>
            <div className="flex gap-4">
              <button
                onClick={() => setCurrentPage('dashboard')}
                className={`px-6 py-3 rounded-lg font-semibold transition-all ${
                  currentPage === 'dashboard'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-700 border border-gray-200'
                }`}
              >
                Dashboard
              </button>
              <button
                onClick={() => setCurrentPage('newsfeed')}
                className={`px-6 py-3 rounded-lg font-semibold transition-all ${
                  currentPage === 'newsfeed'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-700 border border-gray-200'
                }`}
              >
                Latest Insights
              </button>
              <button
                onClick={() => setCurrentPage('research')}
                className={`px-6 py-3 rounded-lg font-semibold transition-all ${
                  currentPage === 'research'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-700 border border-gray-200'
                }`}
              >
                Research Hub
              </button>
            </div>
          </div>
          <p className="text-gray-600 text-lg">
            {currentPage === 'dashboard' 
              ? 'Focus on what\'s driving your deals' 
              : currentPage === 'newsfeed'
              ? 'Real-time customer feedback from win-loss interviews'
              : 'Advanced research and analysis tools'
            }
          </p>
        </div>

        {/* Dashboard Content */}
        {currentPage === 'dashboard' && (
          <>
            <div className="grid grid-cols-2 gap-8 mb-8">
              
              {/* Why You're Losing Deals */}
              <div className="relative overflow-hidden bg-white/70 backdrop-blur-sm rounded-3xl shadow-2xl border border-rose-200/50">
                <div className="absolute inset-0 bg-gradient-to-br from-rose-500/10 via-rose-400/5 to-transparent"></div>
                
                <div className="relative bg-gradient-to-r from-rose-500 via-rose-600 to-rose-700 p-8">
                  <div className="flex items-center gap-4">
                    <div className="w-14 h-14 bg-white/20 backdrop-blur-sm rounded-2xl flex items-center justify-center shadow-lg">
                      <span className="text-3xl">🚨</span>
                    </div>
                    <div>
                      <h2 className="text-3xl font-bold text-white mb-1">Why You're Losing Deals</h2>
                      <p className="text-rose-100 font-medium">High-impact factors hurting your win rate</p>
                    </div>
                  </div>
                </div>
                
                <div className="relative p-8 space-y-5">
                  {factors.filter(f => f.trend === 'declining').map(factor => (
                    <div 
                      key={factor.name}
                      className="bg-white rounded-2xl shadow-sm cursor-pointer transition-all duration-200 border border-slate-200/50 p-6 hover:shadow-md hover:border-slate-300/70"
                      onClick={() => setExpandedView(factor.name)}
                    >
                      <h4 className="font-bold text-slate-900 mb-6 text-lg">{factor.name}</h4>
                      
                      <div className="flex justify-between items-start mb-6">
                        <div>
                          <div className="text-slate-500 text-sm font-medium uppercase tracking-wide mb-3">TREND</div>
                          <div className="flex items-center gap-3">
                            <div className="w-12 h-12 bg-red-100 rounded-xl flex items-center justify-center">
                              <span className="text-xl text-red-500">↘️</span>
                            </div>
                            <span className="font-bold text-xl text-red-500">Losing Ground</span>
                          </div>
                        </div>
                        
                        <div className="text-right">
                          <div className="text-slate-500 text-sm font-medium uppercase tracking-wide mb-3">ARR IMPACT</div>
                          <div className="font-bold text-slate-900 text-3xl">{formatARR(factor.arrImpact)}</div>
                        </div>
                      </div>
                      
                      <div>
                        <div className="text-slate-500 text-sm font-medium uppercase tracking-wide mb-2">CUSTOMERS</div>
                        <div className="text-slate-700 font-medium">{factor.customers.join(', ')}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              
              {/* Why You're Winning Deals */}
              <div className="relative overflow-hidden bg-white/70 backdrop-blur-sm rounded-3xl shadow-2xl border border-emerald-200/50">
                <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/10 via-emerald-400/5 to-transparent"></div>
                
                <div className="relative bg-gradient-to-r from-emerald-500 via-emerald-600 to-emerald-700 p-8">
                  <div className="flex items-center gap-4">
                    <div className="w-14 h-14 bg-white/20 backdrop-blur-sm rounded-2xl flex items-center justify-center shadow-lg">
                      <span className="text-3xl">🚀</span>
                    </div>
                    <div>
                      <h2 className="text-3xl font-bold text-white mb-1">Why You're Winning Deals</h2>
                      <p className="text-emerald-100 font-medium">High-impact factors driving your success</p>
                    </div>
                  </div>
                </div>
                
                <div className="relative p-8 space-y-5">
                  {factors.filter(f => f.trend === 'improving').map(factor => (
                    <div 
                      key={factor.name}
                      className="bg-white rounded-2xl shadow-sm cursor-pointer transition-all duration-200 border border-slate-200/50 p-6 hover:shadow-md hover:border-slate-300/70"
                      onClick={() => setExpandedView(factor.name)}
                    >
                      <h4 className="font-bold text-slate-900 mb-6 text-lg">{factor.name}</h4>
                      
                      <div className="flex justify-between items-start mb-6">
                        <div>
                          <div className="text-slate-500 text-sm font-medium uppercase tracking-wide mb-3">TREND</div>
                          <div className="flex items-center gap-3">
                            <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center">
                              <span className="text-xl text-green-500">↗️</span>
                            </div>
                            <span className="font-bold text-xl text-green-500">Gaining Edge</span>
                          </div>
                        </div>
                        
                        <div className="text-right">
                          <div className="text-slate-500 text-sm font-medium uppercase tracking-wide mb-3">ARR IMPACT</div>
                          <div className="font-bold text-slate-900 text-3xl">{formatARR(factor.arrImpact)}</div>
                        </div>
                      </div>
                      
                      <div>
                        <div className="text-slate-500 text-sm font-medium uppercase tracking-wide mb-2">CUSTOMERS</div>
                        <div className="text-slate-700 font-medium">{factor.customers.join(', ')}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </>
        )}

        {/* Expanded View Modal */}
        {expandedView && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-start justify-center p-4 pt-8">
            <div className="bg-white rounded-3xl shadow-2xl w-full max-w-7xl h-[85vh] overflow-hidden">
              <div className="bg-gradient-to-r from-slate-700 to-slate-800 p-4 flex justify-between items-center">
                <div className="flex items-center gap-4">
                  <button
                    onClick={() => setExpandedView(null)}
                    className="flex items-center gap-2 text-white/80 hover:text-white transition-all hover:bg-white/10 rounded-xl px-3 py-2"
                  >
                    <span className="text-lg">←</span>
                    <span className="font-medium">Back to Dashboard</span>
                  </button>
                  <div className="w-px h-6 bg-white/20"></div>
                  <h2 className="text-xl font-bold text-white">{expandedView}</h2>
                </div>
                <button
                  onClick={() => setExpandedView(null)}
                  className="text-white/80 hover:text-white text-2xl w-8 h-8 flex items-center justify-center rounded-full hover:bg-white/10 transition-all"
                >
                  ×
                </button>
              </div>
              
              <div className="flex h-full">
                <div className="flex-1 p-8 bg-slate-50">
                  <h3 className="text-xl font-bold text-slate-800 mb-6">Performance Timeline</h3>
                  
                  <div className="bg-white rounded-2xl p-6 mb-6 shadow-sm">
                    <div className="flex justify-between items-center mb-4">
                      <span className="text-sm font-medium text-slate-600">6-Month Trend</span>
                      <div className="flex items-center gap-2">
                        <span className="text-2xl text-red-500">↘️</span>
                        <span className="font-bold text-red-500">Losing Ground</span>
                      </div>
                    </div>
                    
                    <div className="h-64 relative">
                      <svg width="100%" height="100%" viewBox="0 0 600 200" className="overflow-visible">
                        {[0, 25, 50, 75, 100].map(y => (
                          <line key={y} x1="50" y1={200 - y * 1.5} x2="550" y2={200 - y * 1.5} stroke="#e2e8f0" strokeWidth="1"/>
                        ))}
                        
                        {['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'].map((month, index) => (
                          <text key={index} x={50 + (index * 100)} y="190" textAnchor="middle" className="text-xs fill-slate-500">
                            {month}
                          </text>
                        ))}
                        
                        <polyline
                          points={[48, 48, 52, 59, 33, 26].map((score, index) => {
                            const x = 50 + (index * 100);
                            const y = 175 - (score * 1.5);
                            return `${x},${y}`;
                          }).join(' ')}
                          fill="none"
                          stroke="#6366f1"
                          strokeWidth="3"
                        />
                        
                        {[48, 48, 52, 59, 33, 26].map((score, index) => {
                          const x = 50 + (index * 100);
                          const y = 175 - (score * 1.5);
                          return (
                            <g key={index}>
                              <circle cx={x} cy={y} r="6" fill="#6366f1" stroke="white" strokeWidth="2"/>
                              <text x={x} y={y - 15} textAnchor="middle" className="text-xs font-semibold fill-slate-700">
                                {score}
                              </text>
                            </g>
                          );
                        })}
                        
                        <g>
                          <line x1="250" y1="20" x2="250" y2="175" stroke="#ef4444" strokeWidth="2" strokeDasharray="5,5"/>
                          <circle cx="250" cy="15" r="8" fill="#ef4444"/>
                          <text x="255" y="10" className="text-xs font-semibold fill-white">!</text>
                          <text x="255" y="30" className="text-xs font-medium fill-red-600">Pricing Change</text>
                        </g>
                      </svg>
                    </div>
                  </div>
                  
                  <div className="bg-white rounded-2xl p-6 shadow-sm">
                    <h4 className="text-lg font-bold text-slate-800 mb-4">Key Insights</h4>
                    <div className="space-y-4">
                      <div className="flex items-start gap-3">
                        <div className="w-2 h-2 bg-red-500 rounded-full mt-2"></div>
                        <div>
                          <div className="font-semibold text-slate-800">Sharp Decline in March</div>
                          <div className="text-slate-600 text-sm">Score dropped from 68 to 45 following pricing restructure</div>
                        </div>
                      </div>
                      <div className="flex items-start gap-3">
                        <div className="w-2 h-2 bg-amber-500 rounded-full mt-2"></div>
                        <div>
                          <div className="font-semibold text-slate-800">Competitor Activity</div>
                          <div className="text-slate-600 text-sm">3 deals lost to CloudSync citing better commercial terms</div>
                        </div>
                      </div>
                      <div className="flex items-start gap-3">
                        <div className="w-2 h-2 bg-blue-500 rounded-full mt-2"></div>
                        <div>
                          <div className="font-semibold text-slate-800">Deal Impact</div>
                          <div className="text-slate-600 text-sm">$649K in affected pipeline</div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div className="w-1/2 p-8 bg-white border-l border-slate-200">
                  <h3 className="text-xl font-bold text-slate-800 mb-6">Customer Evidence</h3>
                  
                  <div className="bg-slate-900 rounded-2xl overflow-hidden mb-6 relative group cursor-pointer">
                    <div className="aspect-video bg-gradient-to-br from-slate-800 to-slate-900 flex items-center justify-center">
                      <div className="text-center">
                        <div className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center mb-4 mx-auto group-hover:bg-white/30 transition-all">
                          <div className="w-0 h-0 border-l-[12px] border-l-white border-t-[8px] border-t-transparent border-b-[8px] border-b-transparent ml-1"></div>
                        </div>
                        <div className="text-white font-semibold">Customer Interview</div>
                        <div className="text-white/70 text-sm">TechFlow Inc • 2:34</div>
                      </div>
                    </div>
                    <div className="absolute bottom-4 left-4 bg-black/50 backdrop-blur-sm rounded-lg px-3 py-1">
                      <span className="text-white text-sm font-medium">Click to play</span>
                    </div>
                  </div>
                  
                  <div className="bg-slate-50 rounded-2xl p-6 mb-6">
                    <div className="flex items-start gap-4 mb-4">
                      <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-blue-600 rounded-full flex items-center justify-center text-white font-bold">
                        SF
                      </div>
                      <div>
                        <div className="font-bold text-slate-800">Sarah Foster</div>
                        <div className="text-slate-600 text-sm">VP of Technology, TechFlow Inc</div>
                        <div className="text-slate-500 text-xs">$850K deal • Lost June 15</div>
                      </div>
                    </div>
                    <div className="text-slate-700 italic leading-relaxed">
                      "The pricing just didn't make sense for our budget. When we compared it to CloudSync, 
                      they were offering similar capabilities for 40% less. We really wanted to go with you guys, 
                      but our CFO couldn't justify the cost difference."
                    </div>
                  </div>
                  
                  <div className="space-y-4">
                    <div className="bg-rose-50 border border-rose-200 rounded-xl p-4">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-rose-600 text-lg">⚠️</span>
                        <span className="font-semibold text-rose-800">Competitive Threat</span>
                      </div>
                      <div className="text-rose-700 text-sm">
                        CloudSync mentioned in 4 recent losses, consistently cited as 30-40% cheaper
                      </div>
                    </div>
                    
                    <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-blue-600 text-lg">💡</span>
                        <span className="font-semibold text-blue-800">Affected Customers</span>
                      </div>
                      <div className="text-blue-700 text-sm">
                        DigitalEdge, TechFlow Inc, MetaScale and 2 others citing similar concerns
                      </div>
                    </div>
                  </div>
                  
                  <div className="mt-8 space-y-3">
                    <button className="w-full bg-violet-600 hover:bg-violet-700 text-white font-semibold py-3 px-4 rounded-xl transition-all">
                      Alert Sales Team
                    </button>
                    <button className="w-full bg-slate-200 hover:bg-slate-300 text-slate-700 font-semibold py-3 px-4 rounded-xl transition-all">
                      Export Customer Quote
                    </button>
                    <button className="w-full bg-slate-200 hover:bg-slate-300 text-slate-700 font-semibold py-3 px-4 rounded-xl transition-all">
                      Schedule Deep Dive
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Latest Insights / Newsfeed Content */}
        {currentPage === 'newsfeed' && (
          <>
            {/* Filters and Controls */}
            <div className="flex justify-between items-center mb-8">
              <div className="flex gap-4">
                <select
                  value={feedFilter}
                  onChange={(e) => setFeedFilter(e.target.value)}
                  className="px-4 py-2 bg-white border border-gray-200 rounded-lg"
                >
                  <option value="all">All Outcomes</option>
                  <option value="wins">Wins Only</option>
                  <option value="losses">Losses Only</option>
                </select>
                
                <select
                  value={timeFilter}
                  onChange={(e) => setTimeFilter(e.target.value)}
                  className="px-4 py-2 bg-white border border-gray-200 rounded-lg"
                >
                  <option value="7days">Last 7 Days</option>
                  <option value="30days">Last 30 Days</option>
                </select>
                
                <div className="flex items-center gap-2 text-gray-500 text-sm">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                  <span>Updated 2 hours ago</span>
                </div>
              </div>
              
              <button className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg">
                Set Up Alerts
              </button>
            </div>
            
            {/* Quote Feed */}
            <div className="max-w-4xl">
              {getNewsfeedQuotes().length === 0 ? (
                <div className="text-center py-16">
                  <div className="text-6xl mb-4 opacity-60">📝</div>
                  <div className="text-gray-600 text-xl font-semibold mb-2">No insights found</div>
                  <div className="text-gray-500">Try adjusting your filters to see more results</div>
                </div>
              ) : (
                quotes.map(quote => (
                  <div key={quote.id} className={`
                    bg-white rounded-2xl shadow-sm border p-6 mb-4 transition-all hover:shadow-md
                    ${quote.outcome === 'loss' ? 'border-red-100 hover:border-red-200' : 'border-green-100 hover:border-green-200'}
                  `}>
                    {/* Header */}
                    <div className="flex justify-between items-start mb-4">
                      <div className="flex items-center gap-3">
                        <h4 className="font-bold text-gray-900">{quote.customerName}</h4>
                        <span className="font-semibold text-gray-700">{quote.dealSize}</span>
                        <span className="bg-blue-100 text-blue-800 text-xs font-bold px-2 py-1 rounded-full">
                          {quote.industry}
                        </span>
                        {new Date() - quote.timestamp < 24 * 60 * 60 * 1000 && (
                          <span className="bg-green-100 text-green-800 text-xs font-bold px-2 py-1 rounded-full">NEW</span>
                        )}
                      </div>
                      <div className="flex items-center gap-3">
                        <span className={`font-bold text-sm px-3 py-1 rounded-full ${
                          quote.outcome === 'win' 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {quote.outcome.toUpperCase()}
                        </span>
                        <span className="text-gray-500 text-sm">{formatTimeAgo(quote.timestamp)}</span>
                      </div>
                    </div>
                    
                    {/* Quote */}
                    <div className="mb-4">
                      <div className="text-gray-700 italic text-lg leading-relaxed">
                        "{quote.quote}"
                      </div>
                    </div>
                    
                    {/* Tags and Info */}
                    <div className="flex justify-between items-end">
                      <div className="flex items-center gap-4">
                        <div className="flex gap-2">
                          {quote.tags && quote.tags.map(tag => (
                            <span key={tag} className="bg-gray-100 text-gray-600 text-xs px-2 py-1 rounded">
                              {tag}
                            </span>
                          ))}
                        </div>
                      </div>
                      <div className="text-gray-500 text-sm">
                        by {quote.interviewer}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </>
        )}

        {/* Research Hub Content - Brittany's Spreadsheet Replacement */}
        {currentPage === 'research' && (
          <div className="flex gap-8">
            
            {/* Left Sidebar - Advanced Filters */}
            <div className="w-80">
              <div className="bg-white rounded-2xl shadow-lg p-6 mb-6">
                <h3 className="text-lg font-bold mb-4">🤖 AI Research Assistant</h3>
                
                <div className="mb-6">
                  <input
                    type="text"
                    placeholder="Ask anything... 'Show me Health & Beauty pricing issues'"
                    className="w-full p-4 border border-gray-200 rounded-lg text-sm"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                  />
                  <div className="mt-2 text-xs text-gray-500">
                    Try: "pricing issues", "integration wins", "competitor mentions"
                  </div>
                </div>

                {/* Quick Research Prompts */}
                <div className="mb-6">
                  <label className="block text-sm font-semibold mb-3">Quick Research</label>
                  <div className="space-y-2">
                    {[
                      'Pricing concerns by industry',
                      'Competitor mentions last 30 days',
                      'Implementation feedback trends',
                      'Product strength highlights'
                    ].map(prompt => (
                      <button
                        key={prompt}
                        onClick={() => setSearchQuery(prompt)}
                        className="w-full text-left p-3 text-sm bg-gray-50 hover:bg-blue-50 hover:text-blue-700 rounded-lg transition-all"
                      >
                        {prompt}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Advanced Filters */}
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-semibold mb-2">Industry Filter</label>
                    <select
                      value={industryFilter}
                      onChange={(e) => setIndustryFilter(e.target.value)}
                      className="w-full p-3 border border-gray-200 rounded-lg text-sm"
                    >
                      <option value="all">All Industries</option>
                      {industries.map(industry => (
                        <option key={industry} value={industry}>{industry}</option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-semibold mb-2">Theme Filter</label>
                    <select className="w-full p-3 border border-gray-200 rounded-lg text-sm">
                      <option value="all">All Themes</option>
                      {themes.map(theme => (
                        <option key={theme} value={theme}>{theme}</option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-semibold mb-2">Follow-up Status</label>
                    <select className="w-full p-3 border border-gray-200 rounded-lg text-sm">
                      <option value="all">All Status</option>
                      <option value="pending">Pending</option>
                      <option value="in-progress">In Progress</option>
                      <option value="completed">Completed</option>
                    </select>
                  </div>
                </div>

                <button
                  onClick={() => {
                    setIndustryFilter('all');
                    setSearchQuery('');
                  }}
                  className="w-full mt-4 bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium py-2 px-4 rounded-lg text-sm"
                >
                  Clear All Filters
                </button>
              </div>
            </div>

            {/* Right Content - Research Results */}
            <div className="flex-1">
              {/* Results Header */}
              <div className="flex justify-between items-center mb-6">
                <div>
                  <h3 className="text-xl font-bold">
                    Research Results ({getFilteredQuotes().length})
                  </h3>
                  {searchQuery && (
                    <p className="text-gray-600 text-sm mt-1">
                      Searching for: "{searchQuery}"
                    </p>
                  )}
                </div>
                
                <div className="flex gap-3">
                  <button className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg text-sm">
                    📄 Export to White Paper
                  </button>
                  <button className="bg-gray-200 hover:bg-gray-300 text-gray-700 font-semibold py-2 px-4 rounded-lg text-sm">
                    💾 Save Search
                  </button>
                </div>
              </div>

              {/* Industry Summary Dashboard - Brittany's Industry Tracker Replacement */}
              {!searchQuery && industryFilter === 'all' && (
                <div className="mb-8">
                  <h4 className="text-lg font-bold mb-4">📊 Industry Intelligence Dashboard</h4>
                  <div className="grid grid-cols-2 gap-4">
                    {industries.map(industry => {
                      const industryQuotes = quotes.filter(q => q.industry === industry);
                      const winRate = industryQuotes.length ? ((industryQuotes.filter(q => q.outcome === 'win').length / industryQuotes.length) * 100).toFixed(0) : 0;
                      const topTheme = themes.find(theme => 
                        industryQuotes.some(q => q.themes?.includes(theme))
                      );
                      const pendingFollowUps = industryQuotes.filter(q => q.followUpStatus === 'pending').length;
                      
                      return (
                        <div key={industry} className="bg-white rounded-xl shadow-sm border p-6 hover:shadow-md transition-all cursor-pointer">
                          <div className="flex justify-between items-start mb-4">
                            <h5 className="font-bold text-lg">{industry}</h5>
                            <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                              pendingFollowUps > 0 ? 'bg-orange-100 text-orange-800' : 'bg-green-100 text-green-800'
                            }`}>
                              {pendingFollowUps} follow-ups
                            </span>
                          </div>
                          <div className="space-y-3">
                            <div className="flex justify-between">
                              <span className="text-gray-600">Total Interviews:</span>
                              <span className="font-semibold">{industryQuotes.length}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-600">Win Rate:</span>
                              <span className={`font-semibold ${winRate > 60 ? 'text-green-600' : winRate > 40 ? 'text-yellow-600' : 'text-red-600'}`}>
                                {winRate}%
                              </span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-600">Top Theme:</span>
                              <span className="text-xs bg-purple-100 text-purple-800 px-2 py-1 rounded font-medium">
                                {topTheme?.replace('#', '') || 'N/A'}
                              </span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-600">Latest Quote:</span>
                              <span className="text-xs text-gray-500">
                                {industryQuotes.length ? formatTimeAgo(industryQuotes[0].timestamp) : 'None'}
                              </span>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Research Quote Results - Enhanced for Brittany's needs */}
              <div>
                <h4 className="text-lg font-bold mb-4">🔍 Detailed Quote Analysis</h4>
                {getFilteredQuotes().length === 0 ? (
                  <div className="text-center py-16">
                    <div className="text-6xl mb-4 opacity-60">🔍</div>
                    <div className="text-gray-600 text-xl font-semibold mb-2">No results found</div>
                    <div className="text-gray-500">Try adjusting your search or filters</div>
                  </div>
                ) : (
                  getFilteredQuotes().map(quote => (
                    <div key={quote.id} className="bg-white rounded-2xl shadow-sm border p-6 mb-4 hover:shadow-md transition-all">
                      {/* Enhanced Header with Industry Focus */}
                      <div className="flex justify-between items-start mb-4">
                        <div className="flex items-center gap-3">
                          <h4 className="font-bold text-gray-900">{quote.customerName}</h4>
                          <span className="font-semibold text-gray-700">{quote.dealSize}</span>
                          <span className="bg-blue-100 text-blue-800 text-xs font-bold px-3 py-1 rounded-full">
                            📍 {quote.industry}
                          </span>
                          <span className={`text-xs font-bold px-3 py-1 rounded-full ${
                            quote.outcome === 'win' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                          }`}>
                            {quote.outcome.toUpperCase()}
                          </span>
                        </div>
                        <div className="text-right">
                          <div className={`text-xs font-medium px-2 py-1 rounded-full mb-1 ${
                            quote.followUpStatus === 'completed' ? 'bg-green-100 text-green-800' :
                            quote.followUpStatus === 'pending' ? 'bg-orange-100 text-orange-800' :
                            'bg-blue-100 text-blue-800'
                          }`}>
                            📋 {quote.followUpStatus?.replace('-', ' ').toUpperCase()}
                          </div>
                          <div className="text-gray-500 text-xs">{formatTimeAgo(quote.timestamp)}</div>
                        </div>
                      </div>
                      
                      {/* Theme Tags - Brittany's Theme Tracker */}
                      <div className="mb-4">
                        <div className="flex flex-wrap gap-2">
                          {quote.themes && quote.themes.map(theme => (
                            <span key={theme} className="bg-purple-100 text-purple-800 text-xs font-medium px-3 py-1 rounded-full">
                              🏷️ {theme}
                            </span>
                          ))}
                        </div>
                      </div>
                      
                      {/* Quote Content */}
                      <div className="mb-4">
                        <div className="text-gray-700 italic text-lg leading-relaxed bg-gray-50 p-4 rounded-lg border-l-4 border-blue-500">
                          "{quote.quote}"
                        </div>
                      </div>
                      
                      {/* Enhanced Bottom Section for Research */}
                      <div className="flex justify-between items-end">
                        <div className="flex items-center gap-4">
                          <div className="flex gap-2">
                            {quote.tags && quote.tags.map(tag => (
                              <span key={tag} className="bg-gray-100 text-gray-600 text-xs px-2 py-1 rounded">
                                #{tag}
                              </span>
                            ))}
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-gray-700 text-sm font-medium">📝 {quote.interviewer}</div>
                          <div className="text-gray-500 text-xs">Research ready for white paper</div>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default WinLossDashboard;