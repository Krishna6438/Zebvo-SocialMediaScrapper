import React, { useState, useEffect } from 'react';
import { 
  Search, RotateCw, Filter, Shield, AlertTriangle, Languages, 
  Download, Layers, MessageSquare, Heart, Share2, Globe, 
  Clock, ChevronDown, ChevronUp, RefreshCw, BarChart2, CheckCircle, HelpCircle
} from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_BASE || (import.meta.env.DEV ? 'http://localhost:8000' : '');

// Platform display metadata
const PLATFORMS = {
  twitter: { name: 'Twitter/X', color: '#1d9bf0', icon: '🐦' },
  reddit: { name: 'Reddit', color: '#ff4500', icon: '👽' },
  facebook: { name: 'Facebook', color: '#1877f2', icon: '👥' },
  instagram: { name: 'Instagram', color: '#e1306c', icon: '📸' },
  linkedin: { name: 'LinkedIn', color: '#0a66c2', icon: '💼' },
  youtube: { name: 'YouTube', color: '#ff0000', icon: '📺' },
  tiktok: { name: 'TikTok', color: '#ff0050', icon: '🎵' }
};

const LANGUAGES_SUPPORTED = [
  { name: 'English', code: 'english' },
  { name: 'Hindi', code: 'hindi' },
  { name: 'Punjabi', code: 'punjabi' },
  { name: 'Spanish', code: 'spanish' },
  { name: 'French', code: 'french' },
  { name: 'German', code: 'german' },
  { name: 'Arabic', code: 'arabic' },
  { name: 'Chinese', code: 'chinese' },
  { name: 'Russian', code: 'russian' },
  { name: 'Japanese', code: 'japanese' }
];

const CATEGORIES = [
  'Application', 'Renewal', 'Appointments', 'Tatkal', 'Visa', 
  'Travel Issues', 'Government Announcements', 'Scams/Fraud', 'News', 'Personal Experiences'
];

function App() {
  // Posts & Stats state
  const [posts, setPosts] = useState([]);
  const [stats, setStats] = useState({
    platforms: {},
    categories: {},
    sentiments: {},
    total_active: 0,
    gibberish_filtered: 0
  });
  
  // Loading & Action states
  const [isLoading, setIsLoading] = useState(true);
  const [isScraping, setIsScraping] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  
  // Filtering & Sorting state
  const [selectedPlatform, setSelectedPlatform] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [selectedSentiment, setSelectedSentiment] = useState('');
  const [selectedRegion, setSelectedRegion] = useState('');
  const [selectedLanguage, setSelectedLanguage] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [showGibberish, setShowGibberish] = useState(false);
  const [clusteredView, setClusteredView] = useState(true);
  
  const [sortBy, setSortBy] = useState('time'); // time or engagement
  const [sortOrder, setSortOrder] = useState('desc');
  
  // Card-specific states
  const [expandedPosts, setExpandedPosts] = useState({}); // { postId: boolean }
  const [translatedTexts, setTranslatedTexts] = useState({}); // { [postId_lang]: string }
  const [cardSelectedLang, setCardSelectedLang] = useState({}); // { postId: lang }
  const [loadingTranslations, setLoadingTranslations] = useState({}); // { [postId_lang]: boolean }
  const [expandedClusters, setExpandedClusters] = useState({}); // { clusterId: boolean }

  // Fetch posts & stats on filter change
  useEffect(() => {
    fetchData();
  }, [
    selectedPlatform, selectedCategory, selectedSentiment, 
    selectedRegion, selectedLanguage, searchQuery, showGibberish, 
    sortBy, sortOrder
  ]);

  const fetchData = async () => {
    setIsLoading(true);
    setErrorMessage('');
    try {
      // Build query string
      const params = new URLSearchParams();
      if (selectedPlatform) params.append('platform', selectedPlatform);
      if (selectedCategory) params.append('category', selectedCategory);
      if (selectedSentiment) params.append('sentiment', selectedSentiment);
      if (selectedRegion) params.append('region', selectedRegion);
      if (selectedLanguage) params.append('language', selectedLanguage);
      if (searchQuery) params.append('search', searchQuery);
      params.append('is_gibberish', showGibberish ? 'true' : 'false');
      params.append('sort_by', sortBy);
      params.append('sort_order', sortOrder);
      
      const postsRes = await fetch(`${API_BASE}/api/posts?${params.toString()}`);
      if (!postsRes.ok) throw new Error('Failed to load posts');
      const postsData = await postsRes.json();
      setPosts(postsData);

      const statsRes = await fetch(`${API_BASE}/api/stats`);
      if (!statsRes.ok) throw new Error('Failed to load stats');
      const statsData = await statsRes.json();
      setStats(statsData);
    } catch (err) {
      setErrorMessage('Unable to connect to the backend server. Make sure it is running on port 8000.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  // Trigger manual scrape
  const handleScrapeTrigger = async () => {
    setIsScraping(true);
    setErrorMessage('');
    try {
      const res = await fetch(`${API_BASE}/api/scrape/trigger`, { method: 'POST' });
      if (!res.ok) throw new Error('Scraping request failed');
      await fetchData();
    } catch (err) {
      setErrorMessage('Scraping trigger failed. Check backend status.');
      console.error(err);
    } finally {
      setIsScraping(false);
    }
  };

  // Translate specific post content
  const handleTranslateCard = async (postId, langCode) => {
    if (langCode === 'english' || !langCode) {
      // Revert to default
      setCardSelectedLang(prev => ({ ...prev, [postId]: '' }));
      return;
    }
    
    const cacheKey = `${postId}_${langCode}`;
    setCardSelectedLang(prev => ({ ...prev, [postId]: langCode }));

    if (translatedTexts[cacheKey]) return; // Already cached locally in memory

    setLoadingTranslations(prev => ({ ...prev, [cacheKey]: true }));
    try {
      const res = await fetch(`${API_BASE}/api/posts/${postId}/translate?lang=${langCode}`);
      if (!res.ok) throw new Error('Translation failed');
      const data = await res.json();
      setTranslatedTexts(prev => ({ ...prev, [cacheKey]: data.translated_text }));
    } catch (err) {
      console.error(err);
      setTranslatedTexts(prev => ({ ...prev, [cacheKey]: 'Failed to translate post. Try again.' }));
    } finally {
      setLoadingTranslations(prev => ({ ...prev, [cacheKey]: false }));
    }
  };

  // Toggle card body expansion
  const toggleExpandPost = (postId) => {
    setExpandedPosts(prev => ({ ...prev, [postId]: !prev[postId] }));
  };

  // Toggle cluster view expand/collapse
  const toggleExpandCluster = (clusterId) => {
    setExpandedClusters(prev => ({ ...prev, [clusterId]: !prev[clusterId] }));
  };

  // Export handlers
  const handleExportCSV = () => {
    const params = new URLSearchParams();
    if (selectedPlatform) params.append('platform', selectedPlatform);
    if (selectedCategory) params.append('category', selectedCategory);
    if (selectedSentiment) params.append('sentiment', selectedSentiment);
    if (selectedRegion) params.append('region', selectedRegion);
    if (selectedLanguage) params.append('language', selectedLanguage);
    if (searchQuery) params.append('search', searchQuery);
    params.append('is_gibberish', showGibberish ? 'true' : 'false');
    window.open(`${API_BASE}/api/export/csv?${params.toString()}`);
  };

  const handleExportPDF = () => {
    const params = new URLSearchParams();
    if (selectedPlatform) params.append('platform', selectedPlatform);
    if (selectedCategory) params.append('category', selectedCategory);
    if (selectedSentiment) params.append('sentiment', selectedSentiment);
    if (selectedRegion) params.append('region', selectedRegion);
    if (selectedLanguage) params.append('language', selectedLanguage);
    if (searchQuery) params.append('search', searchQuery);
    params.append('is_gibberish', showGibberish ? 'true' : 'false');
    window.open(`${API_BASE}/api/export/pdf?${params.toString()}`);
  };

  // Render platform badge
  const renderPlatformBadge = (platformName) => {
    const info = PLATFORMS[platformName.toLowerCase()] || { name: platformName, color: '#64748b', icon: '🔗' };
    return (
      <span style={{ 
        display: 'inline-flex', 
        alignItems: 'center', 
        gap: '4px',
        padding: '4px 10px',
        borderRadius: '6px',
        fontSize: '11px',
        fontWeight: '600',
        backgroundColor: `${info.color}15`,
        color: info.color,
        border: `1px solid ${info.color}30`
      }}>
        <span>{info.icon}</span>
        <span>{info.name}</span>
      </span>
    );
  };

  // Render single post card component
  const renderPostCard = (post, isClusteredSubpost = false) => {
    const isExpanded = expandedPosts[post.id] || false;
    const activeLang = cardSelectedLang[post.id] || '';
    const translationKey = `${post.id}_${activeLang}`;
    const translationText = translatedTexts[translationKey] || '';
    const isTranslating = loadingTranslations[translationKey] || false;
    
    // Get sentiment color and label class
    let sentimentClass = 'sentiment-neu';
    if (post.sentiment === 'Positive') sentimentClass = 'sentiment-pos';
    if (post.sentiment === 'Negative') sentimentClass = 'sentiment-neg';

    return (
      <div 
        key={post.id} 
        className={`glass-panel ${sentimentClass}`}
        style={{ 
          padding: '20px', 
          display: 'flex', 
          flexDirection: 'column', 
          gap: '16px',
          marginLeft: isClusteredSubpost ? '24px' : '0',
          borderLeftWidth: '5px',
          animation: 'fadeIn 0.5s ease'
        }}
      >
        {/* Card Header */}
        <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'center', gap: '10px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{ width: '40px', height: '40px', borderRadius: '50%', backgroundColor: 'rgba(15,23,42,0.03)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '18px', border: '1px solid var(--border-glass)' }}>
              {PLATFORMS[post.platform.toLowerCase()]?.icon || '🔗'}
            </div>
            <div>
              <div style={{ fontWeight: '600', fontSize: '14px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                {post.username}
                <span style={{ color: 'var(--color-text-muted)', fontSize: '12px', fontWeight: '400' }}>
                  {post.user_handle}
                </span>
              </div>
              <div style={{ fontSize: '11px', color: 'var(--color-text-muted)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Clock size={11} />
                {new Date(post.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} ({new Date(post.timestamp).toLocaleDateString()})
              </div>
            </div>
          </div>
          
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <span style={{ fontSize: '11px', padding: '3px 8px', borderRadius: '4px', backgroundColor: 'rgba(15,23,42,0.03)', border: '1px solid var(--border-glass)', color: 'var(--color-text-secondary)', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Globe size={11} />
              {post.region}
            </span>
            <span style={{ fontSize: '11px', padding: '3px 8px', borderRadius: '4px', background: 'var(--gradient-main)', color: 'white', fontWeight: '600' }}>
              {post.category}
            </span>
          </div>
        </div>

        {/* Content Body */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {/* AI Summary Block */}
          {!post.is_gibberish && (
            <div style={{ 
              background: 'linear-gradient(to right, rgba(99, 102, 241, 0.05), rgba(168, 85, 247, 0.05))',
              border: '1px dashed var(--border-glass-glow)',
              borderRadius: '10px',
              padding: '12px 16px'
            }}>
              <div style={{ fontSize: '11px', fontWeight: '800', color: '#a855f7', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <Shield size={12} /> AI Summary (~30 words)
              </div>
              <p style={{ fontSize: '13.5px', color: 'var(--color-text-primary)', lineHeight: '1.5', fontStyle: 'italic' }}>
                "{post.summary}"
              </p>
            </div>
          )}

          {/* Full content toggler */}
          <div style={{ borderTop: '1px solid rgba(255,255,255,0.03)', paddingTop: '10px' }}>
            <button 
              onClick={() => toggleExpandPost(post.id)}
              style={{ background: 'none', border: 'none', color: 'var(--color-primary)', fontSize: '12px', fontWeight: '600', cursor: 'pointer', display: 'inline-flex', alignItems: 'center', gap: '4px', marginBottom: '8px' }}
            >
              <span>{isExpanded ? 'Hide Original Text' : 'View Original Text'}</span>
              {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
            </button>
            
            {isExpanded && (
              <p style={{ 
                fontSize: '13px', 
                color: 'var(--color-text-secondary)', 
                lineHeight: '1.6', 
                whiteSpace: 'pre-wrap',
                background: 'rgba(15,23,42,0.03)',
                padding: '12px',
                borderRadius: '8px',
                border: '1px solid var(--border-glass)'
              }}>
                {post.content}
              </p>
            )}
          </div>

          {/* Translation Result Block */}
          {activeLang && (
            <div style={{ 
              backgroundColor: 'rgba(20, 184, 166, 0.04)',
              border: '1px solid rgba(20, 184, 166, 0.2)',
              borderRadius: '8px',
              padding: '12px',
              marginTop: '4px'
            }}>
              <div style={{ fontSize: '11px', fontWeight: '700', color: 'var(--color-accent)', textTransform: 'uppercase', marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Languages size={12} /> Translated to {LANGUAGES_SUPPORTED.find(l => l.code === activeLang)?.name}
              </div>
              {isTranslating ? (
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', color: 'var(--color-text-muted)' }}>
                  <RefreshCw size={12} className="animate-spin" style={{ animation: 'spin 1.5s linear infinite' }} />
                  Translating...
                </div>
              ) : (
                <p style={{ fontSize: '13px', color: 'var(--color-text-primary)', lineHeight: '1.5' }}>
                  {translationText}
                </p>
              )}
            </div>
          )}
        </div>

        {/* Card Footer Actions */}
        <div style={{ 
          display: 'flex', 
          flexWrap: 'wrap', 
          justifyContent: 'space-between', 
          alignItems: 'center', 
          borderTop: '1px solid var(--border-glass)', 
          paddingTop: '12px',
          gap: '12px'
        }}>
          {/* Engagement Metrics */}
          <div style={{ display: 'flex', gap: '16px', fontSize: '12px', color: 'var(--color-text-secondary)' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }} title="Likes">
              <Heart size={14} style={{ color: post.likes > 0 ? '#ef4444' : 'inherit' }} />
              {post.likes}
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }} title="Comments">
              <MessageSquare size={14} />
              {post.comments}
            </span>
            <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }} title="Shares">
              <Share2 size={14} />
              {post.shares}
            </span>
          </div>

          {/* Translation Dropdown Widget */}
          {!post.is_gibberish && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Languages size={13} style={{ color: 'var(--color-text-muted)' }} />
              <select 
                value={activeLang} 
                onChange={(e) => handleTranslateCard(post.id, e.target.value)}
                style={{ 
                  backgroundColor: 'rgba(15,23,42,0.04)', 
                  border: '1px solid var(--border-glass)', 
                  color: 'var(--color-text-primary)',
                  fontSize: '12px',
                  padding: '4px 8px',
                  borderRadius: '6px',
                  outline: 'none',
                  cursor: 'pointer'
                }}
              >
                <option value="">Original Language</option>
                {LANGUAGES_SUPPORTED.map(l => (
                  <option key={l.code} value={l.code}>
                    {l.name}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>
      </div>
    );
  };

  // Group posts by clusters
  const getClusteredGroups = () => {
    const clusters = {};
    const unclustered = [];
    
    posts.forEach(post => {
      if (post.cluster_id !== null && post.cluster_id !== undefined) {
        if (!clusters[post.cluster_id]) {
          clusters[post.cluster_id] = [];
        }
        clusters[post.cluster_id].push(post);
      } else {
        unclustered.push(post);
      }
    });
    
    return { clusters, unclustered };
  };

  const { clusters, unclustered } = getClusteredGroups();

  return (
    <div className="dashboard-container">
      {/* Background radial overlays */}
      <div className="glow-bg">
        <div className="glow-circle-1"></div>
        <div className="glow-circle-2"></div>
      </div>

      {/* SIDEBAR */}
      <aside className="sidebar">
        {/* Logo block */}
        <div>
          <h2 style={{ 
            fontSize: '22px', 
            background: 'var(--gradient-main)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}>
            🛂 Zebvo Newswire
          </h2>
          <p style={{ color: 'var(--color-text-muted)', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.1em', marginTop: '4px', paddingLeft: '2px' }}>
            Passport Analytics Shield
          </p>
        </div>

        {/* System Pulse badge */}
        <div className="glass-panel" style={{ padding: '12px 16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span className="pulse-badge">
            <span className="pulse-dot"></span>
            Real-Time Scraper
          </span>
          <button 
            onClick={handleScrapeTrigger}
            disabled={isScraping}
            className="btn-secondary"
            style={{ padding: '6px 10px', borderRadius: '6px', fontSize: '11px' }}
            title="Force run scraping cycle"
          >
            {isScraping ? (
              <RefreshCw size={12} className="animate-spin" style={{ animation: 'spin 1.5s linear infinite' }} />
            ) : (
              <RotateCw size={12} />
            )}
          </button>
        </div>

        {/* FILTERS PANEL */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '18px', flexGrow: 1 }}>
          <h3 style={{ fontSize: '12px', textTransform: 'uppercase', color: 'var(--color-text-muted)', letterSpacing: '0.08em', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Filter size={12} /> Filters & Engine
          </h3>
          
          {/* Platforms selector */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <label style={{ fontSize: '11px', color: 'var(--color-text-secondary)', fontWeight: '600' }}>Social Source</label>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px' }}>
              <button 
                onClick={() => setSelectedPlatform('')}
                className={selectedPlatform === '' ? 'btn-primary' : 'btn-secondary'}
                style={{ padding: '8px', fontSize: '11px', borderRadius: '8px' }}
              >
                All Sources
              </button>
              {Object.keys(PLATFORMS).map(key => (
                <button 
                  key={key}
                  onClick={() => setSelectedPlatform(key)}
                  className={selectedPlatform === key ? 'btn-primary' : 'btn-secondary'}
                  style={{ 
                    padding: '8px', 
                    fontSize: '11px', 
                    borderRadius: '8px',
                    borderColor: selectedPlatform === key ? 'transparent' : `${PLATFORMS[key].color}25`,
                    color: selectedPlatform === key ? 'white' : 'var(--color-text-primary)'
                  }}
                >
                  {PLATFORMS[key].icon} {PLATFORMS[key].name.split('/')[0]}
                </button>
              ))}
            </div>
          </div>

          {/* Category Dropdown */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <label style={{ fontSize: '11px', color: 'var(--color-text-secondary)', fontWeight: '600' }}>Topic Category</label>
            <select 
              value={selectedCategory} 
              onChange={(e) => setSelectedCategory(e.target.value)}
              style={{ backgroundColor: 'rgba(15,23,42,0.04)', border: '1px solid var(--border-glass)', borderRadius: '8px', padding: '10px', color: 'var(--color-text-primary)', fontSize: '12px', outline: 'none', width: '100%' }}
            >
              <option value="">All Categories</option>
              {CATEGORIES.map(cat => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          </div>

          {/* Sentiment Dropdown */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <label style={{ fontSize: '11px', color: 'var(--color-text-secondary)', fontWeight: '600' }}>Sentiment Tone</label>
            <select 
              value={selectedSentiment} 
              onChange={(e) => setSelectedSentiment(e.target.value)}
              style={{ backgroundColor: 'rgba(15,23,42,0.04)', border: '1px solid var(--border-glass)', borderRadius: '8px', padding: '10px', color: 'var(--color-text-primary)', fontSize: '12px', outline: 'none' }}
            >
              <option value="">All Sentiments</option>
              <option value="Positive">🟢 Positive</option>
              <option value="Neutral">🟡 Neutral</option>
              <option value="Negative">🔴 Negative</option>
            </select>
          </div>

          {/* Region Filter */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <label style={{ fontSize: '11px', color: 'var(--color-text-secondary)', fontWeight: '600' }}>Region / Country</label>
            <select 
              value={selectedRegion} 
              onChange={(e) => setSelectedRegion(e.target.value)}
              style={{ backgroundColor: 'rgba(15,23,42,0.04)', border: '1px solid var(--border-glass)', borderRadius: '8px', padding: '10px', color: 'var(--color-text-primary)', fontSize: '12px', outline: 'none' }}
            >
              <option value="">All Regions</option>
              <option value="India">India</option>
              <option value="USA">USA</option>
              <option value="Spain">Spain</option>
              <option value="Japan">Japan</option>
              <option value="Global">Global</option>
            </select>
          </div>

          {/* Original Language Filter */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <label style={{ fontSize: '11px', color: 'var(--color-text-secondary)', fontWeight: '600' }}>Original Language</label>
            <select 
              value={selectedLanguage} 
              onChange={(e) => setSelectedLanguage(e.target.value)}
              style={{ backgroundColor: 'rgba(15,23,42,0.04)', border: '1px solid var(--border-glass)', borderRadius: '8px', padding: '10px', color: 'var(--color-text-primary)', fontSize: '12px', outline: 'none' }}
            >
              <option value="">All Languages</option>
              <option value="English">English</option>
              <option value="Hindi">Hindi</option>
              <option value="Punjabi">Punjabi</option>
              <option value="Spanish">Spanish</option>
              <option value="Japanese">Japanese</option>
            </select>
          </div>

          {/* Sort Settings */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: '12px' }}>
            <label style={{ fontSize: '11px', color: 'var(--color-text-secondary)', fontWeight: '600' }}>Sort Metrics</label>
            <div style={{ display: 'flex', gap: '4px' }}>
              <select 
                value={sortBy} 
                onChange={(e) => setSortBy(e.target.value)}
                style={{ flexGrow: 1, backgroundColor: 'rgba(15,23,42,0.04)', border: '1px solid var(--border-glass)', borderRadius: '8px', padding: '8px', color: 'var(--color-text-primary)', fontSize: '11px', outline: 'none' }}
              >
                <option value="time">🕒 Time Published</option>
                <option value="engagement">🔥 Engagement</option>
              </select>
              <select 
                value={sortOrder} 
                onChange={(e) => setSortOrder(e.target.value)}
                style={{ backgroundColor: 'rgba(15,23,42,0.04)', border: '1px solid var(--border-glass)', borderRadius: '8px', padding: '8px', color: 'var(--color-text-primary)', fontSize: '11px', outline: 'none' }}
              >
                <option value="desc">↓ Desc</option>
                <option value="asc">↑ Asc</option>
              </select>
            </div>
          </div>

          {/* Gibberish filter toggler */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: '12px' }}>
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <span style={{ fontSize: '12px', fontWeight: '600', color: 'var(--color-text-secondary)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <Shield size={13} style={{ color: 'var(--color-accent)' }} /> Spam Filter Active
              </span>
              <span style={{ fontSize: '10px', color: 'var(--color-text-muted)' }}>Show blocked gibberish</span>
            </div>
            <label className="switch">
              <input 
                type="checkbox" 
                checked={showGibberish} 
                onChange={(e) => setShowGibberish(e.target.checked)}
              />
              <span className="slider"></span>
            </label>
          </div>
        </div>

        {/* Footer info */}
        <div style={{ borderTop: '1px solid var(--border-glass)', paddingTop: '16px', fontSize: '11px', color: 'var(--color-text-muted)', display: 'flex', flexDirection: 'column', gap: '4px' }}>
          <span>© 2026 Zebvo Newswire Ltd.</span>
          <span>Jalandhar, Punjab, India</span>
        </div>
      </aside>

      {/* MAIN CONTENT WORKSPACE */}
      <main className="main-content">
        {/* Top Header Grid */}
        <header style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'center', gap: '16px' }}>
          {/* Search bar */}
          <div className="glass-panel" style={{ display: 'flex', alignItems: 'center', padding: '0 16px', width: '100%', maxWidth: '480px', height: '48px' }}>
            <Search size={18} style={{ color: 'var(--color-text-muted)', marginRight: '12px' }} />
            <input 
              type="text" 
              placeholder="Search keywords across original & translated text..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{ background: 'none', border: 'none', color: 'var(--color-text-primary)', outline: 'none', fontSize: '14px', width: '100%' }}
            />
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            {/* Clustered View Switch */}
            <div className="glass-panel" style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '8px 16px', height: '48px' }}>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start' }}>
                <span style={{ fontSize: '12px', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <Layers size={13} style={{ color: 'var(--color-primary)' }} /> Clustered View
                </span>
                <span style={{ fontSize: '9px', color: 'var(--color-text-muted)' }}>Collapse similar posts</span>
              </div>
              <label className="switch">
                <input 
                  type="checkbox" 
                  checked={clusteredView} 
                  onChange={(e) => setClusteredView(e.target.checked)}
                />
                <span className="slider"></span>
              </label>
            </div>

            {/* Export buttons */}
            <div style={{ display: 'flex', gap: '8px' }}>
              <button onClick={handleExportCSV} className="btn-secondary" style={{ height: '48px', fontSize: '12px' }}>
                <Download size={14} /> CSV
              </button>
              <button onClick={handleExportPDF} className="btn-secondary" style={{ height: '48px', fontSize: '12px' }}>
                <Download size={14} /> PDF Report
              </button>
            </div>
          </div>
        </header>

        {/* Error notification if server is disconnected */}
        {errorMessage && (
          <div style={{ backgroundColor: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239, 68, 68, 0.4)', borderRadius: '12px', padding: '16px', color: '#f87171', display: 'flex', alignItems: 'center', gap: '12px', fontSize: '13px' }}>
            <AlertTriangle size={18} />
            <div>
              <strong>Connection Error:</strong> {errorMessage}
            </div>
          </div>
        )}

        {/* ANALYTICS ROW */}
        <section className="stats-grid">
          {/* Widget 1: Social Platform Split */}
          <div className="glass-panel chart-container">
            <h4 className="chart-title">Source Platforms</h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', flexGrow: 1, justifyContent: 'center' }}>
              {Object.keys(PLATFORMS).map(platform => {
                const count = stats.platforms[platform] || 0;
                const total = stats.total_active || 1;
                const percent = Math.round((count / total) * 100);
                const info = PLATFORMS[platform];
                return (
                  <div key={platform} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontSize: '14px', width: '20px' }}>{info.icon}</span>
                    <div style={{ flexGrow: 1 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', marginBottom: '2px' }}>
                        <span style={{ fontWeight: '500' }}>{info.name.split('/')[0]}</span>
                        <span style={{ color: 'var(--color-text-secondary)' }}>{count} ({percent}%)</span>
                      </div>
                      <div style={{ height: '6px', backgroundColor: 'rgba(15,23,42,0.05)', borderRadius: '3px', overflow: 'hidden' }}>
                        <div style={{ width: `${percent}%`, height: '100%', backgroundColor: info.color, borderRadius: '3px', boxShadow: `0 0 8px ${info.color}50` }}></div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Widget 2: Sentiment Split */}
          <div className="glass-panel chart-container">
            <h4 className="chart-title">Public Sentiment</h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', flexGrow: 1, justifyContent: 'center' }}>
              <div style={{ display: 'flex', height: '28px', borderRadius: '14px', overflow: 'hidden', border: '1px solid var(--border-glass)', boxShadow: 'inset 0 1px 3px rgba(15,23,42,0.1)' }}>
                {['Positive', 'Neutral', 'Negative'].map(sent => {
                  const count = stats.sentiments[sent] || 0;
                  const total = stats.total_active || 1;
                  const percent = (count / total) * 100;
                  const colors = {
                    Positive: 'var(--color-sentiment-pos)',
                    Neutral: 'var(--color-sentiment-neu)',
                    Negative: 'var(--color-sentiment-neg)'
                  };
                  if (count === 0) return null;
                  return (
                    <div 
                      key={sent} 
                      style={{ 
                        width: `${percent}%`, 
                        backgroundColor: colors[sent], 
                        display: 'flex', 
                        alignItems: 'center', 
                        justifyContent: 'center',
                        fontSize: '9px',
                        fontWeight: '800',
                        color: '#000',
                        boxShadow: `inset 0 0 10px rgba(0,0,0,0.2)`
                      }}
                      title={`${sent}: ${count} posts`}
                    >
                      {percent > 12 ? `${Math.round(percent)}%` : ''}
                    </div>
                  );
                })}
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-around', gap: '8px' }}>
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                  <span style={{ fontSize: '10px', color: 'var(--color-text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--color-sentiment-pos)' }}></span> Positive
                  </span>
                  <span style={{ fontSize: '16px', fontWeight: '700', fontFamily: 'var(--font-title)' }}>
                    {stats.sentiments['Positive'] || 0}
                  </span>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                  <span style={{ fontSize: '10px', color: 'var(--color-text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--color-sentiment-neu)' }}></span> Neutral
                  </span>
                  <span style={{ fontSize: '16px', fontWeight: '700', fontFamily: 'var(--font-title)' }}>
                    {stats.sentiments['Neutral'] || 0}
                  </span>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                  <span style={{ fontSize: '10px', color: 'var(--color-text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: 'var(--color-sentiment-neg)' }}></span> Negative
                  </span>
                  <span style={{ fontSize: '16px', fontWeight: '700', fontFamily: 'var(--font-title)' }}>
                    {stats.sentiments['Negative'] || 0}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Widget 3: Spam Shield Indicator */}
          <div className="glass-panel chart-container" style={{ background: 'linear-gradient(135deg, rgba(13, 148, 136, 0.05) 0%, rgba(255, 255, 255, 0.65) 100%)' }}>
            <h4 className="chart-title">Spam Shield Efficiency</h4>
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flexGrow: 1, justifyContent: 'center' }}>
              <div style={{ position: 'relative', width: '80px', height: '80px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                {/* SVG circular progress indicator */}
                <svg width="80" height="80" viewBox="0 0 36 36">
                  <path
                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    fill="none"
                    stroke="rgba(15,23,42,0.05)"
                    strokeWidth="3.5"
                  />
                  <path
                    d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    fill="none"
                    stroke="var(--color-accent)"
                    strokeWidth="3.5"
                    strokeDasharray={`${Math.round(((stats.gibberish_filtered) / (stats.total_active + stats.gibberish_filtered || 1)) * 100)}, 100`}
                    strokeLinecap="round"
                    style={{ filter: 'drop-shadow(0px 0px 4px var(--color-accent))' }}
                  />
                </svg>
                <div style={{ position: 'absolute', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                  <Shield size={20} style={{ color: 'var(--color-accent)', filter: 'drop-shadow(0 0 4px rgba(20,184,166,0.3))' }} />
                </div>
              </div>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <div style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>
                  Total Scraped: <span style={{ color: 'var(--color-text-primary)', fontWeight: '600' }}>{stats.total_active + stats.gibberish_filtered}</span>
                </div>
                <div style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>
                  Gibberish Filtered: <span style={{ color: '#f43f5e', fontWeight: '600' }}>{stats.gibberish_filtered}</span>
                </div>
                <div style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>
                  Clean Dashboard: <span style={{ color: 'var(--color-sentiment-pos)', fontWeight: '600' }}>{stats.total_active}</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* FEED SECTION */}
        <section style={{ display: 'flex', flexDirection: 'column', gap: '16px', minHeight: '400px' }}>
          {isLoading ? (
            // Skeleton Loader
            Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="glass-panel shimmer" style={{ height: '180px', borderRadius: '16px' }}></div>
            ))
          ) : posts.length === 0 ? (
            // Empty state
            <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '60px 20px', textAlign: 'center', gap: '12px' }}>
              <HelpCircle size={48} style={{ color: 'var(--color-text-muted)', animation: 'pulse-animation 2s infinite' }} />
              <h3 style={{ fontSize: '18px' }}>No Passport Posts Found</h3>
              <p style={{ color: 'var(--color-text-secondary)', maxWidth: '400px', fontSize: '13px' }}>
                We couldn't find any posts matching your active filters from the last 24 hours. Trigger the scraper or loosen your filters.
              </p>
              <button onClick={handleScrapeTrigger} disabled={isScraping} className="btn-primary" style={{ marginTop: '8px' }}>
                {isScraping ? 'Refreshing Feed...' : 'Trigger Scraper Run'}
              </button>
            </div>
          ) : (
            // Render posts feed
            <>
              {/* Clustered View */}
              {clusteredView ? (
                <>
                  {/* Clustered Threads */}
                  {Object.keys(clusters).map(clusterId => {
                    const clusterPosts = clusters[clusterId];
                    const isExpanded = expandedClusters[clusterId] || false;
                    const representative = clusterPosts[0]; // First post acts as representative
                    
                    return (
                      <div key={`cluster-${clusterId}`} style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                        {/* Cluster Header Card */}
                        <div 
                          className="glass-panel" 
                          onClick={() => toggleExpandCluster(clusterId)}
                          style={{ 
                            padding: '16px 20px', 
                            cursor: 'pointer',
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            borderLeft: '5px solid var(--color-primary)',
                            background: 'linear-gradient(90deg, rgba(99, 102, 241, 0.08) 0%, var(--bg-glass) 100%)'
                          }}
                        >
                          <div style={{ display: 'flex', alignItems: 'center', gap: '14px', flexGrow: 1 }}>
                            <div style={{ backgroundColor: 'rgba(99, 102, 241, 0.15)', width: '32px', height: '32px', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                              <Layers size={16} style={{ color: 'var(--color-primary)' }} />
                            </div>
                            <div style={{ flexGrow: 1 }}>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                                <span style={{ fontWeight: '700', fontSize: '14px', color: 'var(--color-text-primary)' }}>
                                  Clustered Event: {representative.category}
                                </span>
                                <span style={{ fontSize: '10px', padding: '2px 8px', borderRadius: '10px', backgroundColor: 'var(--color-primary)', color: 'white', fontWeight: '800' }}>
                                  {clusterPosts.length} similar reports
                                </span>
                              </div>
                              <p style={{ fontSize: '12px', color: 'var(--color-text-secondary)', marginTop: '2px', fontStyle: 'italic' }}>
                                "{representative.summary}"
                              </p>
                            </div>
                          </div>
                          
                          <button style={{ background: 'none', border: 'none', color: 'var(--color-text-muted)', cursor: 'pointer' }}>
                            {isExpanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                          </button>
                        </div>

                        {/* Cluster Sub-cards (visible when expanded) */}
                        {isExpanded && (
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', borderLeft: '2px dashed rgba(99, 102, 241, 0.2)', marginLeft: '16px', paddingLeft: '4px' }}>
                            {clusterPosts.map(post => renderPostCard(post, true))}
                          </div>
                        )}
                      </div>
                    );
                  })}
                  
                  {/* Unclustered individual posts */}
                  {unclustered.map(post => renderPostCard(post, false))}
                </>
              ) : (
                // Flat View: render all posts directly
                posts.map(post => renderPostCard(post, false))
              )}
            </>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;
