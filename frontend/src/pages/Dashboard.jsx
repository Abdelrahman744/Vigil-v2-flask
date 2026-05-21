import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, Trash2, Activity, Globe, LogOut, CheckCircle2, XCircle, Clock, Search, ExternalLink } from 'lucide-react';
import { format } from 'date-fns';
import api from '../api';

export default function Dashboard() {
  const [targets, setTargets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [newTargetName, setNewTargetName] = useState('');
  const [newTargetUrl, setNewTargetUrl] = useState('');
  const [addLoading, setAddLoading] = useState(false);
  const [selectedTarget, setSelectedTarget] = useState(null);
  const [targetLogs, setTargetLogs] = useState([]);
  const [logsLoading, setLogsLoading] = useState(false);
  
  const navigate = useNavigate();

  useEffect(() => {
    fetchTargets();
  }, []);

  const fetchTargets = async () => {
    try {
      const res = await api.get('/targets');
      setTargets(res.data.targets);
    } catch (err) {
      if (err.response?.status === 401) handleLogout();
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await api.post('/logout');
    } catch (err) {
      console.error(err);
    }
    localStorage.removeItem('token');
    navigate('/login');
  };

  const handleAddTarget = async (e) => {
    e.preventDefault();
    setAddLoading(true);

    // Auto-prepend https:// if the user didn't include a protocol
    let finalUrl = newTargetUrl.trim();
    if (!/^https?:\/\//i.test(finalUrl)) {
      finalUrl = `https://${finalUrl}`;
    }

    try {
      await api.post('/targets', { name: newTargetName, url: finalUrl });
      setIsAddModalOpen(false);
      setNewTargetName('');
      setNewTargetUrl('');
      fetchTargets();
    } catch (err) {
      alert(err.response?.data?.message || 'Failed to add target');
    } finally {
      setAddLoading(false);
    }
  };

  const handleDeleteTarget = async (id, e) => {
    e.stopPropagation();
    if (!window.confirm('Are you sure you want to delete this target?')) return;
    try {
      await api.delete(`/targets/${id}`);
      fetchTargets();
    } catch (err) {
      alert('Failed to delete target');
    }
  };

  const openLogsModal = async (target) => {
    setSelectedTarget(target);
    setLogsLoading(true);
    try {
      const res = await api.get(`/targets/${target.id}/logs`);
      setTargetLogs(res.data.logs);
    } catch (err) {
      alert('Failed to fetch logs');
      setSelectedTarget(null);
    } finally {
      setLogsLoading(false);
    }
  };

  const handleManualPing = async (target, e) => {
    e.stopPropagation();
    try {
      await api.post(`/targets/${target.id}/ping`);
      fetchTargets();
    } catch (err) {
      console.error('Ping failed:', err);
    }
  };

  return (
    <div className="min-h-screen bg-background relative">
      {/* Top Navbar */}
      <nav className="border-b border-gray-800 bg-surface/50 backdrop-blur-md sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-secondary flex items-center justify-center">
                <ShieldCheck size={20} className="text-white" />
              </div>
              <span className="text-xl font-bold text-white tracking-tight">Vigil</span>
            </div>
            <button 
              onClick={handleLogout}
              className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors"
            >
              <LogOut size={18} />
              <span>Sign out</span>
            </button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8 gap-4">
          <div>
            <h1 className="text-3xl font-bold text-white">Dashboard</h1>
            <p className="text-gray-400 mt-1">Monitor your websites in real-time</p>
          </div>
          <button 
            onClick={() => setIsAddModalOpen(true)}
            className="bg-primary hover:bg-blue-600 text-white px-5 py-2.5 rounded-xl font-medium transition-colors flex items-center gap-2 shadow-lg shadow-primary/20"
          >
            <Plus size={20} />
            Add Target
          </button>
        </div>

        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="glass-panel p-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-blue-500/10 text-blue-400 rounded-xl">
                <Globe size={24} />
              </div>
              <div>
                <p className="text-gray-400 text-sm font-medium">Total Targets</p>
                <p className="text-3xl font-bold text-white">{targets.length}</p>
              </div>
            </div>
          </div>
          <div className="glass-panel p-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-green-500/10 text-green-400 rounded-xl">
                <CheckCircle2 size={24} />
              </div>
              <div>
                <p className="text-gray-400 text-sm font-medium">Healthy</p>
                <p className="text-3xl font-bold text-white">
                  {targets.filter(t => t.status === 'Up').length}
                </p>
              </div>
            </div>
          </div>
          <div className="glass-panel p-6">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-red-500/10 text-red-400 rounded-xl">
                <XCircle size={24} />
              </div>
              <div>
                <p className="text-gray-400 text-sm font-medium">Down</p>
                <p className="text-3xl font-bold text-white">
                  {targets.filter(t => t.status === 'Down').length}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Target List */}
        {loading ? (
          <div className="flex justify-center py-20">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"></div>
          </div>
        ) : targets.length === 0 ? (
          <div className="glass-panel text-center py-20 flex flex-col items-center">
            <div className="w-16 h-16 bg-gray-800 rounded-full flex items-center justify-center mb-4">
              <Globe size={32} className="text-gray-500" />
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">No targets yet</h3>
            <p className="text-gray-400 mb-6">Add your first website to start monitoring.</p>
            <button 
              onClick={() => setIsAddModalOpen(true)}
              className="bg-gray-800 hover:bg-gray-700 text-white px-6 py-2 rounded-lg transition-colors"
            >
              Add Target
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
            <AnimatePresence>
              {targets.map((target) => (
                <motion.div
                  key={target.id}
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  onClick={() => openLogsModal(target)}
                  className="glass-panel p-6 cursor-pointer hover:border-gray-600 transition-all group relative overflow-hidden"
                >
                  <div className={`absolute top-0 left-0 w-1 h-full ${target.status === 'Up' ? 'bg-green-500' : target.status === 'Down' ? 'bg-red-500' : 'bg-yellow-500'}`} />
                  
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h3 className="text-lg font-bold text-white truncate max-w-[200px]">{target.name}</h3>
                      <a href={target.url} target="_blank" rel="noreferrer" onClick={e => e.stopPropagation()} className="text-sm text-gray-400 hover:text-primary flex items-center gap-1 truncate max-w-[200px]">
                        {target.url}
                        <ExternalLink size={12} />
                      </a>
                    </div>
                    <div className={`px-3 py-1 rounded-full text-xs font-medium flex items-center gap-1.5 ${
                      target.status === 'Up' ? 'bg-green-500/10 text-green-400 border border-green-500/20' : 
                      target.status === 'Down' ? 'bg-red-500/10 text-red-400 border border-red-500/20' : 
                      'bg-yellow-500/10 text-yellow-400 border border-yellow-500/20'
                    }`}>
                      <div className={`w-2 h-2 rounded-full ${target.status === 'Up' ? 'bg-green-400 animate-pulse' : target.status === 'Down' ? 'bg-red-400' : 'bg-yellow-400'}`} />
                      {target.status}
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4 mt-6">
                    <div className="bg-black/20 rounded-lg p-3">
                      <p className="text-xs text-gray-500 mb-1">Availability</p>
                      <p className="text-lg font-semibold text-white">{target.stats?.availability || 'N/A'}</p>
                    </div>
                    <div className="bg-black/20 rounded-lg p-3">
                      <p className="text-xs text-gray-500 mb-1">Avg Response</p>
                      <p className="text-lg font-semibold text-white">{target.stats?.averageLatency ? `${target.stats.averageLatency}ms` : 'N/A'}</p>
                    </div>
                  </div>

                  <div className="mt-6 flex justify-between items-center pt-4 border-t border-gray-800">
                    <div className="flex items-center gap-1.5 text-xs text-gray-500">
                      <Clock size={14} />
                      <span>{target.last_checked ? format(new Date(target.last_checked), 'MMM d, h:mm a') : 'Never'}</span>
                    </div>
                    <div className="flex gap-2">
                      <button 
                        onClick={(e) => handleManualPing(target, e)}
                        className="p-2 text-gray-400 hover:text-blue-400 hover:bg-blue-400/10 rounded-lg transition-colors"
                        title="Manual Ping"
                      >
                        <Activity size={16} />
                      </button>
                      <button 
                        onClick={(e) => handleDeleteTarget(target.id, e)}
                        className="p-2 text-gray-400 hover:text-red-400 hover:bg-red-400/10 rounded-lg transition-colors"
                        title="Delete Target"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        )}
      </main>

      {/* Add Target Modal */}
      <AnimatePresence>
        {isAddModalOpen && (
          <>
            <motion.div 
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
              onClick={() => setIsAddModalOpen(false)}
            />
            <motion.div 
              initial={{ opacity: 0, scale: 0.95, y: 20 }} animate={{ opacity: 1, scale: 1, y: 0 }} exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-md z-50 p-4"
            >
              <div className="glass-panel p-6">
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-xl font-bold text-white">Add New Target</h2>
                  <button onClick={() => setIsAddModalOpen(false)} className="text-gray-400 hover:text-white">
                    <XCircle size={24} />
                  </button>
                </div>
                <form onSubmit={handleAddTarget} className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-400 mb-1">Friendly Name</label>
                    <input 
                      type="text" required value={newTargetName} onChange={e => setNewTargetName(e.target.value)}
                      placeholder="e.g., Production API"
                      className="w-full bg-black/20 border border-gray-700 rounded-xl py-2.5 px-4 text-white placeholder-gray-600 focus:border-primary focus:ring-1 focus:ring-primary outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-400 mb-1">URL to Monitor</label>
                    <input 
                      type="text" required value={newTargetUrl} onChange={e => setNewTargetUrl(e.target.value)}
                      placeholder="example.com"
                      className="w-full bg-black/20 border border-gray-700 rounded-xl py-2.5 px-4 text-white placeholder-gray-600 focus:border-primary focus:ring-1 focus:ring-primary outline-none"
                    />
                  </div>
                  <button type="submit" disabled={addLoading} className="w-full bg-primary text-white font-medium py-3 rounded-xl mt-4 hover:bg-blue-600 transition-colors">
                    {addLoading ? 'Adding & Checking...' : 'Add Target'}
                  </button>
                </form>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* Logs Modal */}
      <AnimatePresence>
        {selectedTarget && (
          <>
            <motion.div 
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
              onClick={() => setSelectedTarget(null)}
            />
            <motion.div 
              initial={{ opacity: 0, x: 100 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 100 }}
              className="fixed top-0 right-0 h-full w-full max-w-lg bg-surface border-l border-gray-800 shadow-2xl z-50 flex flex-col"
            >
              <div className="p-6 border-b border-gray-800 flex justify-between items-center">
                <div>
                  <h2 className="text-xl font-bold text-white">{selectedTarget.name}</h2>
                  <p className="text-sm text-gray-400 truncate max-w-[300px]">{selectedTarget.url}</p>
                </div>
                <button onClick={() => setSelectedTarget(null)} className="p-2 text-gray-400 hover:bg-gray-800 rounded-full transition-colors">
                  <XCircle size={24} />
                </button>
              </div>
              
              <div className="flex-1 overflow-y-auto p-6 space-y-4">
                {logsLoading ? (
                  <div className="flex justify-center py-10">
                    <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-primary"></div>
                  </div>
                ) : targetLogs.length === 0 ? (
                  <p className="text-center text-gray-500 py-10">No logs recorded yet.</p>
                ) : (
                  targetLogs.map(log => (
                    <div key={log.id} className="bg-black/20 border border-gray-800 rounded-xl p-4 flex items-start gap-4">
                      <div className={`mt-1 w-2.5 h-2.5 rounded-full flex-shrink-0 ${log.status === 'Up' ? 'bg-green-500' : 'bg-red-500'}`} />
                      <div className="flex-1 min-w-0">
                        <div className="flex justify-between items-start mb-1">
                          <span className="font-medium text-white">{log.status}</span>
                          <span className="text-xs text-gray-500">{format(new Date(log.timestamp), 'MMM d, HH:mm:ss')}</span>
                        </div>
                        <div className="text-sm text-gray-400 mb-2">{log.details}</div>
                        <div className="flex gap-3 text-xs">
                          {log.response_time > 0 && (
                            <span className="bg-gray-800 text-gray-300 px-2 py-1 rounded-md">{log.response_time}ms</span>
                          )}
                          {log.status_code && (
                            <span className="bg-gray-800 text-gray-300 px-2 py-1 rounded-md">HTTP {log.status_code}</span>
                          )}
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}

// Temporary ShieldCheck icon since it wasn't imported from lucide-react at the top
const ShieldCheck = ({ size, className }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
    <path d="m9 12 2 2 4-4"/>
  </svg>
);
