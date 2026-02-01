'use client';

import React, { useState, useEffect } from 'react';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area,
  Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis
} from 'recharts';
import { 
  AlertTriangle, 
  TrendingUp, 
  Target, 
  Zap, 
  Shield, 
  BarChart3,
  Cpu,
  BrainCircuit,
  Maximize2,
  ChevronRight,
  RefreshCcw,
  Eye,
  Swords,
  Activity
} from 'lucide-react';
import { motion } from 'framer-motion';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState('macro');
  const [isSimulated, setIsSimulated] = useState(false);
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [matchId, setMatchId] = useState('test-match-123');
  const [selectedPlayer, setSelectedPlayer] = useState<number>(1);

  useEffect(() => {
    setLoading(true);
    setError(null);
    fetch(`http://localhost:8000/api/match/${matchId}/review`)
      .then(res => {
        if (!res.ok) throw new Error(`Backend error: ${res.statusText}`);
        return res.json();
      })
      .then(d => {
        setData(d);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to fetch match review", err);
        setError(err.message);
        setLoading(false);
      });
  }, [matchId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#050a14] flex flex-col items-center justify-center">
        <Cpu className="w-16 h-16 text-primary animate-pulse mb-4" />
        <p className="text-primary font-mono tracking-widest animate-pulse uppercase">Initializing Neural Link...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-[#050a14] flex flex-col items-center justify-center p-6 text-center">
        <AlertTriangle className="w-16 h-16 text-red-500 mb-4" />
        <h2 className="text-2xl font-bold text-white mb-2">NEURAL LINK FAILURE</h2>
        <p className="text-slate-400 mb-8 max-w-md">Failed to establish connection with the decision engine. Ensure the backend is running on port 8000.</p>
        <div className="bg-red-500/10 border border-red-500/30 p-4 rounded-lg mb-8 font-mono text-xs text-red-400">
          ERROR: {error}
        </div>
        <button 
          onClick={() => window.location.reload()}
          className="px-8 py-3 bg-primary text-black font-bold uppercase rounded-full hover:scale-105 transition-transform"
        >
          Retry Connection
        </button>
      </div>
    );
  }

  const chartData = data?.timeline_snapshots?.map((s: any) => ({
    time: `${Math.floor(s.timestamp / 60000)}:00`,
    prob: 0.5 + (s.gold_diff / 10000), // Adjusted for visual
    goldDiff: s.gold_diff,
    xpDiff: s.xp_diff
  })) || [
    { time: '0:00', prob: 0.50, goldDiff: 0, xpDiff: 0 },
  ];

  return (
    <div className="min-h-screen bg-[#050a14] text-slate-100 cyber-grid p-6 font-sans">
      {/* Header */}
      <header className="flex justify-between items-center mb-8 border-b border-blue-900/50 pb-4">
        <div className="flex items-center gap-3">
          <div className="bg-primary/20 p-2 rounded-lg border border-primary/50">
            <Cpu className="text-primary w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-black tracking-tighter italic">DECISION<span className="text-primary italic">LENS</span></h1>
            <p className="text-xs text-slate-500 uppercase tracking-widest font-bold">Assistant Coach v1.0 // Cloud9 Edition</p>
          </div>
        </div>
        <div className="flex gap-6">
           <div className="hidden md:flex items-center gap-2 px-4 py-2 bg-slate-900/50 border border-slate-800 rounded-lg">
             <div className="text-right">
               <p className="text-[10px] text-slate-500 uppercase font-bold">Match ID</p>
               <input 
                 value={matchId} 
                 onChange={(e) => setMatchId(e.target.value)}
                 className="text-xs font-mono text-primary bg-transparent border-none focus:outline-none w-32"
               />
             </div>
           </div>
          <div className="text-right">
            <p className="text-[10px] text-slate-500 uppercase font-bold tracking-widest">Decision Status</p>
            <p className="text-sm font-black text-primary animate-pulse italic">OPTIMIZING</p>
          </div>
        </div>
      </header>

      <main className="grid grid-cols-12 gap-6">
        {/* Left Column: Stats & Chart */}
        <div className="col-span-12 lg:col-span-8 space-y-6">
          <div className="grid grid-cols-4 gap-4">
             {[
               { label: 'Gold Diff', value: data?.current_state?.gold_diff || 0, icon: <TrendingUp className="w-4 h-4"/>, color: 'text-yellow-500' },
               { label: 'XP Diff', value: data?.current_state?.xp_diff || 0, icon: <Zap className="w-4 h-4"/>, color: 'text-blue-500' },
               { label: 'Dragons', value: data?.current_state?.dragons_diff || 0, icon: <Target className="w-4 h-4"/>, color: 'text-red-500' },
               { label: 'Kills', value: `${data?.current_state?.team100_kills || 0} / ${data?.current_state?.team200_kills || 0}`, icon: <Shield className="w-4 h-4"/>, color: 'text-green-500' },
             ].map((stat, i) => (
               <div key={i} className="glass-panel p-4 rounded-xl border-l-2 border-primary/50">
                 <div className="flex items-center gap-2 mb-1">
                   <div className={`${stat.color}`}>{stat.icon}</div>
                   <p className="text-[10px] font-bold text-slate-500 uppercase">{stat.label}</p>
                 </div>
                 <p className="text-xl font-black italic">{stat.value}</p>
               </div>
             ))}
          </div>

          {/* Main Visualizer */}
          <div className="glass-panel p-6 rounded-2xl relative overflow-hidden">
            <div className="absolute top-0 left-0 w-1 h-full bg-primary" />
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-lg font-bold flex items-center gap-2">
                <BarChart3 className="text-primary w-5 h-5" />
                WIN PROBABILITY TELEMETRY
              </h2>
              <div className="flex gap-2">
                <span className="px-3 py-1 bg-primary/10 text-primary border border-primary/20 rounded text-[10px] font-bold">XGBOOST ENGINE</span>
                <span className="px-3 py-1 bg-slate-800 text-slate-400 rounded text-[10px] font-bold uppercase tracking-tighter">Live Inference</span>
              </div>
            </div>
            
            <div className="h-[300px] w-full mt-4">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData}>
                  <defs>
                    <linearGradient id="colorProb" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#00a3ff" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#00a3ff" stopOpacity={0}/>
                    </linearGradient>
                    <linearGradient id="colorGold" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#eab308" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#eab308" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                  <XAxis dataKey="time" stroke="#475569" fontSize={12} tickLine={false} axisLine={false} />
                  <YAxis yAxisId="left" domain={[0, 1]} stroke="#475569" fontSize={12} tickLine={false} axisLine={false} />
                  <YAxis yAxisId="right" orientation="right" stroke="#475569" fontSize={12} tickLine={false} axisLine={false} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '8px' }}
                    itemStyle={{ color: '#00a3ff' }}
                  />
                  <Area yAxisId="left" type="monotone" dataKey="prob" stroke="#00a3ff" strokeWidth={3} fillOpacity={1} fill="url(#colorProb)" name="Win Prob" />
                  <Area yAxisId="right" type="monotone" dataKey="goldDiff" stroke="#eab308" strokeWidth={2} fillOpacity={1} fill="url(#colorGold)" name="Gold Diff" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Bottom Grid: Insights Tabs */}
          <div className="glass-panel rounded-2xl p-1">
            <div className="flex border-b border-blue-900/50 overflow-x-auto">
              {['macro', 'micro', 'efficiency', 'team', 'what-if'].map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`px-6 py-4 text-sm font-bold uppercase tracking-wider transition-all whitespace-nowrap ${
                    activeTab === tab 
                    ? 'text-primary border-b-2 border-primary' 
                    : 'text-slate-500 hover:text-slate-300'
                  }`}
                >
                  {tab === 'efficiency' ? 'Player Stats' : tab === 'team' ? 'Team Performance' : `${tab} Review`}
                </button>
              ))}
            </div>
            
            <div className="p-6">
              {activeTab === 'macro' && (
                <div className="space-y-4">
                  {data?.macro_insights?.map((m: any, i: number) => (
                    <div key={i} className="flex items-start gap-4 p-4 rounded-xl bg-slate-900/50 border border-slate-800 hover:border-primary/30 transition-colors">
                      <div className="bg-primary/20 p-2 rounded-lg"><TrendingUp className="text-primary w-5 h-5"/></div>
                      <div className="flex-1">
                        <div className="flex justify-between">
                          <h4 className="font-bold text-slate-100 uppercase text-sm tracking-tight">{m.type}</h4>
                          <span className="font-mono text-xs text-primary bg-primary/10 px-2 py-0.5 rounded">
                            {Math.floor(m.timestamp / 60000)}:{(Math.floor(m.timestamp % 60000 / 1000)).toString().padStart(2, '0')}
                          </span>
                        </div>
                        <p className="text-sm text-slate-400 mt-1">{m.description}</p>
                      </div>
                    </div>
                  ))}
                  {(!data?.macro_insights || data.macro_insights.length === 0) && (
                    <p className="text-center text-slate-500 py-8 italic">No macro inflections detected in this snapshot.</p>
                  )}
                </div>
              )}
              
              {activeTab === 'micro' && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {data?.micro_insights?.map((mistake: any, i: number) => (
                    <div key={i} className="p-4 rounded-xl bg-slate-900/50 border border-slate-800 flex justify-between items-center group hover:border-red-500/30 transition-colors">
                      <div className="flex gap-3 items-center">
                        <div className="w-8 h-8 rounded bg-red-500/10 flex items-center justify-center font-bold text-red-500 text-xs">ERR</div>
                        <div>
                          <p className="text-xs font-bold text-slate-500 uppercase">Player {mistake.player_id}</p>
                          <p className="text-sm font-medium">{mistake.type}</p>
                          <p className="text-[10px] text-slate-600 font-mono mt-1">TS: {Math.floor(mistake.timestamp / 60000)}m</p>
                        </div>
                      </div>
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase ${
                        mistake.impact === 'High' ? 'bg-red-500/20 text-red-500' : 'bg-slate-700 text-slate-300'
                      }`}>
                        {mistake.impact}
                      </span>
                    </div>
                  ))}
                   {(!data?.micro_insights || data.micro_insights.length === 0) && (
                    <p className="text-center text-slate-500 py-8 italic col-span-2">No individual mistakes identified.</p>
                  )}
                </div>
              )}

              {activeTab === 'efficiency' && (
                <div className="grid grid-cols-12 gap-6">
                  <div className="col-span-12 xl:col-span-8 overflow-x-auto">
                    <table className="w-full text-left">
                      <thead>
                        <tr className="text-[10px] font-bold text-slate-500 uppercase tracking-widest border-b border-slate-800">
                          <th className="pb-4">Player</th>
                          <th className="pb-4">Team</th>
                          <th className="pb-4 text-right">GPM</th>
                          <th className="pb-4 text-right">Gold</th>
                          <th className="pb-4 text-right">CS/M</th>
                          <th className="pb-4 text-right">Efficiency</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800">
                        {data?.player_stats?.map((p: any) => (
                          <tr 
                            key={p.player_id} 
                            onClick={() => setSelectedPlayer(p.player_id)}
                            className={`group hover:bg-slate-900/50 transition-colors cursor-pointer ${selectedPlayer === p.player_id ? 'bg-primary/5 border-l-2 border-primary' : ''}`}
                          >
                            <td className="py-4 font-bold text-sm pl-2">Player {p.player_id}</td>
                            <td className="py-4 text-xs uppercase font-bold">
                              <span className={p.team_id === 100 ? 'text-blue-500' : 'text-red-500'}>
                                {p.team_id === 100 ? 'Blue' : 'Red'}
                              </span>
                            </td>
                            <td className="py-4 text-right font-mono text-sm">{p.gpm.toFixed(0)}</td>
                            <td className="py-4 text-right font-mono text-sm">{p.total_gold.toLocaleString()}</td>
                            <td className="py-4 text-right font-mono text-sm">{p.cs_per_min?.toFixed(1) || '0.0'}</td>
                            <td className="py-4 text-right">
                               <div className="flex items-center justify-end gap-2">
                                 <div className="w-16 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                                   <div className="h-full bg-primary" style={{ width: `${p.efficiency_score}%` }} />
                                 </div>
                                 <span className="font-bold text-xs">{p.efficiency_score}%</span>
                               </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  <div className="col-span-12 xl:col-span-4 space-y-4">
                    <div className="bg-slate-900/40 p-6 rounded-2xl border border-slate-800 h-full">
                      <h3 className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-6">Player {selectedPlayer} Performance</h3>
                      
                      <div className="h-[250px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                          <RadarChart cx="50%" cy="50%" outerRadius="80%" data={[
                            { subject: 'GPM', A: data?.player_stats?.find((p:any) => p.player_id === selectedPlayer)?.gpm / 10, fullMark: 100 },
                            { subject: 'KP%', A: data?.player_stats?.find((p:any) => p.player_id === selectedPlayer)?.kill_participation, fullMark: 100 },
                            { subject: 'Vision', A: data?.player_stats?.find((p:any) => p.player_id === selectedPlayer)?.vision_score * 2, fullMark: 100 },
                            { subject: 'Damage', A: data?.player_stats?.find((p:any) => p.player_id === selectedPlayer)?.damage_share * 4, fullMark: 100 },
                            { subject: 'Efficiency', A: data?.player_stats?.find((p:any) => p.player_id === selectedPlayer)?.efficiency_score, fullMark: 100 },
                          ]}>
                            <PolarGrid stroke="#1e293b" />
                            <PolarAngleAxis dataKey="subject" tick={{ fill: '#475569', fontSize: 10 }} />
                            <Radar
                              name={`Player ${selectedPlayer}`}
                              dataKey="A"
                              stroke="#00a3ff"
                              fill="#00a3ff"
                              fillOpacity={0.5}
                            />
                          </RadarChart>
                        </ResponsiveContainer>
                      </div>

                      <div className="grid grid-cols-2 gap-4 mt-6">
                        <div className="p-3 bg-slate-800/40 rounded-lg">
                          <p className="text-[10px] text-slate-500 uppercase font-bold">Vision Score</p>
                          <p className="text-lg font-black text-primary italic">{data?.player_stats?.find((p:any) => p.player_id === selectedPlayer)?.vision_score}</p>
                        </div>
                        <div className="p-3 bg-slate-800/40 rounded-lg">
                          <p className="text-[10px] text-slate-500 uppercase font-bold">KP %</p>
                          <p className="text-lg font-black text-primary italic">{data?.player_stats?.find((p:any) => p.player_id === selectedPlayer)?.kill_participation}%</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'team' && (
                <div className="space-y-8">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    <div className="bg-slate-900/40 p-6 rounded-2xl border border-slate-800">
                      <h3 className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-6">Gold Distribution</h3>
                      <div className="h-[200px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                          <LineChart data={chartData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                            <XAxis dataKey="time" stroke="#475569" fontSize={10} hide />
                            <YAxis stroke="#475569" fontSize={10} />
                            <Tooltip contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b' }} />
                            <Line type="monotone" dataKey="goldDiff" stroke="#00a3ff" strokeWidth={2} dot={false} />
                          </LineChart>
                        </ResponsiveContainer>
                      </div>
                      <p className="text-[10px] text-slate-500 mt-4 text-center">Relative Gold Advantage over Time</p>
                    </div>

                    <div className="bg-slate-900/40 p-6 rounded-2xl border border-slate-800">
                      <h3 className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-6">Objective Control Rate</h3>
                      <div className="space-y-4">
                        {[
                          { label: 'Blue Dragon Control', val: 60, color: 'bg-blue-500' },
                          { label: 'Red Dragon Control', val: 40, color: 'bg-red-500' },
                          { label: 'Blue Tower Control', val: 75, color: 'bg-blue-500' },
                          { label: 'Red Tower Control', val: 25, color: 'bg-red-500' },
                        ].map((obj, i) => (
                          <div key={i} className="space-y-1">
                            <div className="flex justify-between text-[10px] font-bold uppercase">
                              <span className="text-slate-400">{obj.label}</span>
                              <span className="text-slate-100">{obj.val}%</span>
                            </div>
                            <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                              <div className={cn("h-full transition-all duration-1000", obj.color)} style={{ width: `${obj.val}%` }} />
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="p-6 rounded-2xl bg-blue-500/5 border border-blue-500/20">
                    <div className="flex items-center gap-3 mb-4">
                      <Activity className="text-primary w-5 h-5" />
                      <h3 className="text-sm font-bold text-slate-100 uppercase tracking-widest">Team Synergy Index</h3>
                    </div>
                    <div className="grid grid-cols-4 gap-4">
                      {[
                        { label: 'Objective Setup', val: '84%', status: 'Excellent' },
                        { label: 'Map Pressure', val: '62%', status: 'Average' },
                        { label: 'Teamfight Prowess', val: '91%', status: 'Elite' },
                        { label: 'Vision Control', val: '45%', status: 'Low' },
                      ].map((stat, i) => (
                        <div key={i} className="text-center">
                          <p className="text-2xl font-black text-primary italic">{stat.val}</p>
                          <p className="text-[10px] text-slate-500 uppercase font-bold mt-1">{stat.label}</p>
                          <span className="text-[8px] px-2 py-0.5 rounded bg-slate-800 text-slate-400 uppercase font-bold">{stat.status}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'what-if' && (
                <div className="space-y-6">
                  <div className="p-6 rounded-2xl border-2 border-dashed border-primary/30 bg-primary/5 text-center">
                    <BrainCircuit className="w-10 h-10 text-primary mx-auto mb-4" />
                    <h3 className="text-xl font-bold italic uppercase tracking-tighter">COUNTERFACTUAL ENGINE</h3>
                    <p className="text-sm text-slate-400 max-w-md mx-auto mt-2">Simulate alternate reality match states to quantify decision impact.</p>
                    
                    <div className="flex justify-center gap-4 mt-8">
                      <button 
                         onClick={() => setIsSimulated(!isSimulated)}
                         className="group flex items-center gap-3 px-10 py-4 bg-primary text-black font-black uppercase italic rounded-full shadow-[0_0_30px_rgba(0,163,255,0.4)] hover:scale-105 transition-all duration-300"
                      >
                        {isSimulated ? 'RESET STATE' : 'RUN SHAP SIMULATION'}
                        <RefreshCcw className={`w-5 h-5 ${isSimulated ? 'animate-spin' : ''}`} />
                      </button>
                    </div>
                  </div>

                  {isSimulated && (
                    <motion.div 
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="p-6 rounded-2xl bg-green-500/10 border border-green-500/30 flex flex-col md:flex-row items-center justify-between gap-6"
                    >
                      <div className="flex items-center gap-5">
                        <div className="bg-green-500/20 p-4 rounded-full shadow-[0_0_15px_rgba(34,197,94,0.4)]">
                          <Target className="text-green-500 w-8 h-8"/>
                        </div>
                        <div>
                          <p className="text-xs font-bold text-green-500 uppercase tracking-widest">Scenario: +1 Dragon Secured</p>
                          <p className="text-2xl font-black italic">WIN PROB: {((data?.decision_analysis?.modified_probability || 0) * 100).toFixed(1)}%</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-8">
                        <div className="text-right">
                          <p className="text-[10px] text-slate-500 font-bold uppercase">Delta Shift</p>
                          <p className="text-2xl font-black text-green-400 italic">+{((data?.decision_analysis?.delta || 0) * 100).toFixed(1)}%</p>
                        </div>
                        <div className="h-10 w-[1px] bg-slate-800 hidden md:block" />
                        <div className="text-right">
                          <p className="text-[10px] text-slate-500 font-bold uppercase">Engine Confidence</p>
                          <p className="text-2xl font-mono font-bold text-slate-200">94.2%</p>
                        </div>
                      </div>
                    </motion.div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right Column: AI Assistant */}
        <div className="col-span-12 lg:col-span-4 space-y-6">
          <div className="glass-panel p-6 rounded-2xl h-full border-r border-primary/30 flex flex-col">
            <h2 className="text-lg font-bold flex items-center gap-2 mb-6 uppercase tracking-tighter">
              <BrainCircuit className="text-primary w-5 h-5 animate-pulse" />
              COACH'S INTELLIGENCE
            </h2>
            
            <div className="space-y-6 flex-1 overflow-auto pr-2 custom-scrollbar">
              <div className="bg-slate-900/80 p-5 rounded-xl border border-slate-800 relative">
                <div className="absolute -top-2 -left-2 bg-primary text-black text-[10px] font-black px-2 py-0.5 italic">NEURAL SUMMARY</div>
                <div className="text-sm leading-relaxed text-slate-300 whitespace-pre-wrap">
                  {data?.ai_coach_summary?.split('\n').map((line: string, i: number) => {
                    if (line.startsWith('###')) return <h3 key={i} className="text-primary font-black italic mt-4 mb-2">{line.replace('### ', '')}</h3>;
                    if (line.startsWith('**')) return <p key={i} className="font-bold text-slate-100 mt-3">{line.replace(/\*\*/g, '')}</p>;
                    return <p key={i} className="mt-1">{line}</p>;
                  })}
                </div>
              </div>

              <div className="space-y-4">
                <h3 className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em]">Priority Action Items</h3>
                {[
                  { icon: <Shield className="w-4 h-4" />, text: 'Address isolated deaths detected' },
                  { icon: <Zap className="w-4 h-4" />, text: 'Optimize Dragon setup rotations' },
                  { icon: <Target className="w-4 h-4" />, text: 'Review mid-game gold lead erosion' }
                ].map((item, i) => (
                  <div key={i} className="flex gap-3 items-center p-3 rounded-lg bg-slate-900/30 border border-slate-800/50 hover:border-primary/50 transition-colors group cursor-pointer">
                    <div className="text-primary group-hover:scale-110 transition-transform">{item.icon}</div>
                    <p className="text-sm font-medium">{item.text}</p>
                    <ChevronRight className="w-4 h-4 text-slate-700 ml-auto group-hover:text-primary transition-colors" />
                  </div>
                ))}
              </div>
            </div>

            <div className="pt-6 mt-auto border-t border-slate-800">
               <button className="w-full py-4 glass-panel border border-primary/30 text-primary text-[10px] font-black uppercase tracking-[0.3em] hover:bg-primary/10 transition-colors flex items-center justify-center gap-2 shadow-[0_0_20px_rgba(0,163,255,0.1)]">
                 EXPOR MATCH REVIEW PDF
                 <Maximize2 className="w-4 h-4" />
               </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
