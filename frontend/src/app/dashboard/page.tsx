'use client';

import React, { useState, useEffect } from 'react';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area,
  Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ReferenceDot, ReferenceLine,
  BarChart, Bar, Cell
} from 'recharts';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
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
  const [activeGame, setActiveGame] = useState('lol');
  const [isSimulated, setIsSimulated] = useState(false);
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [matchId, setMatchId] = useState('4063857');
  const [selectedPlayer, setSelectedPlayer] = useState<number>(1);
  const [simulationResult, setSimulationResult] = useState<any>(null);
  const [isSimulating, setIsSimulating] = useState(false);
  const [currentTimeIndex, setCurrentTimeIndex] = useState(-1);
  const [isLive, setIsLive] = useState(false);
  const [liveMatches, setLiveMatches] = useState<any[]>([]);

  useEffect(() => {
    fetch(`http://localhost:8000/api/matches/live?game=${activeGame}`)
      .then(res => res.json())
      .then(setLiveMatches)
      .catch(console.error);
  }, [activeGame]);

  useEffect(() => {
    let interval: any;
    if (isLive && data?.timeline_snapshots) {
      interval = setInterval(() => {
        setCurrentTimeIndex(prev => {
          const next = prev + 1;
          if (next >= data.timeline_snapshots.length) {
            setIsLive(false);
            return prev;
          }
          return next;
        });
      }, 5000);
    }
    return () => clearInterval(interval);
  }, [isLive, data]);

  const currentData = (isLive && currentTimeIndex >= 0 && data?.timeline_snapshots) 
    ? { ...data, 
        current_state: {
          ...data.current_state,
          win_prob: data.timeline_snapshots[currentTimeIndex].win_prob,
          gold_diff: data.timeline_snapshots[currentTimeIndex].gold_diff,
          xp_diff: data.timeline_snapshots[currentTimeIndex].xp_diff,
          timestamp: data.timeline_snapshots[currentTimeIndex].timestamp
        },
        player_stats: data.timeline_snapshots[currentTimeIndex].player_stats,
        shap_explanations: data.timeline_snapshots[currentTimeIndex].shap_explanations,
        macro_insights: data.macro_insights?.filter((m: any) => m.timestamp <= data.timeline_snapshots[currentTimeIndex].timestamp),
        micro_insights: data.micro_insights?.filter((m: any) => m.timestamp <= data.timeline_snapshots[currentTimeIndex].timestamp),
        current_snapshot: data.timeline_snapshots[currentTimeIndex]
      } 
    : {
        ...data,
        current_snapshot: data?.timeline_snapshots?.[data.timeline_snapshots.length - 1]
      };

  const handleSimulate = async (modifications: any) => {
    if (!data?.current_state) return;
    setIsSimulating(true);
    setIsLive(false); // Disable live stream when simulating
    try {
      const baseState = simulationResult?.modified_state || data.current_state;
      const res = await fetch('http://localhost:8000/api/simulate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          current_state: baseState,
          modifications
        })
      });
      const result = await res.json();
      setSimulationResult(result);
      setIsSimulated(true);
    } catch (err) {
      console.error("Simulation failed", err);
    } finally {
      setIsSimulating(false);
    }
  };

  const handleGameSwitch = (game: string) => {
    setActiveGame(game);
    if (game === 'lol') {
      setMatchId('4063857');
    } else {
      setMatchId('val-match-1');
    }
  };

  useEffect(() => {
    setLoading(true);
    setError(null);
    setIsSimulated(false);
    setSimulationResult(null);
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

  const snapshotsToUse = (isLive && currentTimeIndex >= 0) 
    ? data?.timeline_snapshots?.slice(0, currentTimeIndex + 1) 
    : data?.timeline_snapshots;

  const chartData = snapshotsToUse?.map((s: any) => {
    const timeInMin = Math.floor(s.timestamp / 60000);
    // Find events at this minute
    const minuteEvents = data?.objectives?.filter((o: any) => Math.floor(o.timestamp / 60000) === timeInMin) || [];
    const kills = data?.micro_insights?.filter((m: any) => Math.floor(m.timestamp / 60000) === timeInMin) || [];
    
    return {
      time: `${timeInMin}:00`,
      timestamp: s.timestamp,
      prob: s.win_prob || 0.5,
      goldDiff: s.gold_diff,
      xpDiff: s.xp_diff,
      event: minuteEvents.length > 0 ? minuteEvents[0].type : null,
      isKill: kills.length > 0
    };
  }) || [
    { time: '0:00', prob: 0.50, goldDiff: 0, xpDiff: 0 },
  ];

  const currentExplanations = isSimulated && simulationResult ? simulationResult.shap_explanations : currentData?.shap_explanations;
  const shapData = currentExplanations ? Object.entries(currentExplanations).map(([name, value]: [string, any]) => ({
    name: name.replace('_diff', '').replace('_', ' ').toUpperCase(),
    value: value
  })).sort((a, b) => Math.abs(b.value) - Math.abs(a.value)) : [];

  return (
    <div className="min-h-screen bg-[#050a14] text-slate-100 cyber-grid p-6 font-sans relative">
      <div className="scanline" />
      
      {/* Header */}
      <header className="flex justify-between items-center mb-8 border-b border-blue-900/50 pb-4 relative z-10">
        <div className="flex items-center gap-3">
          <div className="bg-primary/20 p-2 rounded-lg border border-primary/50">
            <Cpu className="text-primary w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-black tracking-tighter italic">DECISION<span className="text-primary italic">LENS</span></h1>
            <p className="text-xs text-slate-500 uppercase tracking-widest font-bold">Assistant Coach v1.0 // Cloud9 Edition</p>
          </div>
        </div>
        
        <div className="flex bg-slate-900/50 p-1 rounded-xl border border-slate-800">
          <button 
            onClick={() => handleGameSwitch('lol')}
            className={cn(
              "px-6 py-2 rounded-lg text-xs font-black uppercase transition-all",
              activeGame === 'lol' ? "bg-primary text-black" : "text-slate-500 hover:text-slate-300"
            )}
          >
            League of Legends
          </button>
          <button 
            onClick={() => handleGameSwitch('valorant')}
            className={cn(
              "px-6 py-2 rounded-lg text-xs font-black uppercase transition-all",
              activeGame === 'valorant' ? "bg-primary text-black" : "text-slate-500 hover:text-slate-300"
            )}
          >
            VALORANT
          </button>
        </div>

        <div className="flex gap-6">
           <div className="flex items-center gap-2">
             <button 
               onClick={() => {
                 const newLiveState = !isLive;
                 setIsLive(newLiveState);
                 if (newLiveState) {
                    setCurrentTimeIndex(0);
                    setIsSimulated(false);
                    setSimulationResult(null);
                 } else {
                    setCurrentTimeIndex(-1);
                 }
               }}
               className={cn(
                 "px-8 py-3 rounded-full text-xs font-black uppercase transition-all flex items-center gap-3 shadow-lg",
                 isLive 
                    ? "bg-red-600 text-white animate-pulse shadow-red-900/40" 
                    : "bg-primary text-black hover:scale-105 active:scale-95 shadow-primary/20"
               )}
             >
               <Activity className={cn("w-4 h-4", isLive ? "animate-spin" : "")} />
               {isLive ? "STOP LIVE STREAM" : "START LIVE STREAM"}
             </button>
           </div>
           
           <div className="hidden md:flex items-center gap-2 px-4 py-2 bg-slate-900/50 border border-slate-800 rounded-lg">
             <div className="text-right">
               <p className="text-[10px] text-slate-500 uppercase font-bold">GRID Series Source</p>
               <select 
                 value={matchId} 
                 onChange={(e) => setMatchId(e.target.value)}
                 className="text-xs font-mono text-primary bg-transparent border-none focus:outline-none w-48 cursor-pointer"
               >
                 <optgroup label="System Simulations" className="bg-slate-900 text-slate-500">
                    <option value="4063857" className="bg-slate-900 text-primary">Mock LoL Match [LPL]</option>
                    <option value="val-match-1" className="bg-slate-900 text-primary">Mock Val Match [VCT]</option>
                 </optgroup>
                 {liveMatches.length > 0 && (
                   <optgroup label="GRID Live Series Feed" className="bg-slate-900 text-slate-500">
                    {liveMatches.map((m: any) => (
                      <option key={m.id} value={m.id} className="bg-slate-900 text-primary">
                        {m.title} ({m.tournament})
                      </option>
                    ))}
                   </optgroup>
                 )}
               </select>
             </div>
             <button 
                onClick={() => setMatchId(matchId)}
                className="p-2 hover:bg-slate-800 rounded-md text-primary transition-colors"
             >
                <RefreshCcw className="w-4 h-4" />
             </button>
           </div>
          <div className="text-right min-w-[150px]">
            <p className="text-[10px] text-slate-500 uppercase font-bold tracking-widest">Decision Status</p>
            <p className={cn(
              "text-lg font-black animate-pulse italic",
              isLive ? "text-red-500" : (isSimulated ? "text-amber-500" : "text-primary")
            )}>
              {isLive ? (
                <>LIVE {((currentData?.current_state?.win_prob || 0.5) * 100).toFixed(1)}%</>
              ) : isSimulated ? (
                <>SIM {((simulationResult?.win_probability || 0) * 100).toFixed(1)}%</>
              ) : (
                <>OPTIMIZING</>
              )}
            </p>
          </div>
        </div>
      </header>

      <main className="grid grid-cols-12 gap-6">
        {/* Left Column: Stats & Chart */}
        <div className="col-span-12 lg:col-span-8 space-y-6">
          <div className="grid grid-cols-4 gap-4">
             {[
               { 
                 label: currentData?.game === 'valorant' ? 'Econ Diff' : 'Gold Diff', 
                 value: currentData?.current_state?.gold_diff || 0, 
                 icon: <TrendingUp className="w-4 h-4"/>, 
                 color: 'text-yellow-500' 
               },
               { 
                 label: currentData?.game === 'valorant' ? 'Loadout Diff' : 'XP Diff', 
                 value: currentData?.current_state?.xp_diff || 0, 
                 icon: <Zap className="w-4 h-4"/>, 
                 color: 'text-blue-500' 
               },
               { 
                 label: currentData?.game === 'valorant' ? 'Spikes' : 'Dragons', 
                 value: currentData?.current_state?.dragons_diff || 0, 
                 icon: <Target className="w-4 h-4"/>, 
                 color: 'text-red-500' 
               },
               { 
                 label: 'Kills', 
                 value: `${currentData?.current_state?.team100_kills || 0} / ${currentData?.current_state?.team200_kills || 0}`, 
                 icon: <Shield className="w-4 h-4"/>, 
                 color: 'text-green-500' 
               },
             ].map((stat, i) => (
               <div key={i} className="glass-panel p-4 rounded-xl border-l-2 border-primary/50 relative overflow-hidden">
                 {isLive && <div className="absolute top-0 right-0 w-1 h-1 bg-red-500 rounded-full m-1 animate-ping" />}
                 <div className="flex items-center gap-2 mb-1">
                   <div className={`${stat.color}`}>{stat.icon}</div>
                   <p className="text-[10px] font-bold text-slate-500 uppercase">{stat.label}</p>
                 </div>
                 <p className="text-xl font-black italic">{typeof stat.value === 'number' && stat.value > 0 ? '+' : ''}{stat.value}</p>
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
              <div className="flex gap-2 items-center">
                {isLive && (
                  <div className="flex items-center gap-2 px-3 py-1 bg-red-500/10 border border-red-500/30 rounded">
                    <div className="w-2 h-2 bg-red-500 rounded-full animate-ping" />
                    <span className="text-[10px] font-black text-red-500">LIVE SCANNING</span>
                  </div>
                )}
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
                  <Area yAxisId="right" type="monotone" dataKey="goldDiff" stroke="#eab308" strokeWidth={2} fillOpacity={1} fill="url(#colorGold)" name={currentData?.game === 'valorant' ? 'Econ Diff' : 'Gold Diff'} />
                  
                  {isLive && currentTimeIndex >= 0 && chartData[currentTimeIndex] && (
                    <ReferenceLine yAxisId="left" x={chartData[currentTimeIndex].time} stroke="#fff" strokeDasharray="5 5" opacity={0.5} />
                  )}

                  {chartData.map((d: any, i: number) => d.event ? (
                    <ReferenceLine key={`line-${i}`} yAxisId="left" x={d.time} stroke="#ef4444" strokeDasharray="3 3" opacity={0.5} />
                  ) : null)}
                  
                  {chartData.map((d: any, i: number) => d.event ? (
                    <ReferenceDot 
                      key={`dot-${i}`}
                      yAxisId="left" 
                      x={d.time} 
                      y={d.prob} 
                      r={6} 
                      fill="#ef4444" 
                      stroke="#fff" 
                    />
                  ) : null)}
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Bottom Grid: Insights Tabs */}
          <div className="glass-panel rounded-2xl p-1">
            <div className="flex border-b border-blue-900/50 overflow-x-auto">
              {['macro', 'micro', 'efficiency', 'vision', 'team', 'draft', 'map', 'what-if'].map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`px-6 py-4 text-sm font-bold uppercase tracking-wider transition-all whitespace-nowrap ${
                    activeTab === tab 
                    ? 'text-primary border-b-2 border-primary' 
                    : 'text-slate-500 hover:text-slate-300'
                  }`}
                >
                  {tab === 'efficiency' ? 'Player Stats' : 
                   tab === 'vision' ? (data?.game === 'valorant' ? 'Economy' : 'Vision & Control') :
                   tab === 'team' ? 'Team Performance' : 
                   tab === 'draft' ? (data?.game === 'valorant' ? 'Agent Selection' : 'Draft Analysis') :
                   tab === 'map' ? 'Live Map' :
                   tab === 'macro' ? (data?.game === 'valorant' ? 'Round Review' : 'Macro Review') :
                   `${tab} Review`}
                </button>
              ))}
            </div>
            
            <div className="p-6">
              {activeTab === 'macro' && (
                <div className="space-y-4">
                  {(isLive ? currentData?.macro_insights?.filter((m: any) => m.timestamp <= currentData.current_state.timestamp) : currentData?.macro_insights)?.map((m: any, i: number) => (
                    <div key={i} className="flex items-start gap-4 p-4 rounded-xl bg-slate-900/50 border border-slate-800 hover:border-primary/30 transition-colors group">
                      <div className="bg-primary/20 p-2 rounded-lg group-hover:bg-primary/30 transition-colors"><TrendingUp className="text-primary w-5 h-5"/></div>
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
                  {(!currentData?.macro_insights || currentData.macro_insights.length === 0) && (
                    <p className="text-center text-slate-500 py-8 italic">No macro inflections detected in this snapshot.</p>
                  )}
                </div>
              )}
              
              {activeTab === 'micro' && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {(isLive ? currentData?.micro_insights?.filter((m: any) => m.timestamp <= currentData.current_state.timestamp) : currentData?.micro_insights)?.map((mistake: any, i: number) => (
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
                   {(!currentData?.micro_insights || currentData.micro_insights.length === 0) && (
                    <p className="text-center text-slate-500 py-8 italic col-span-2">No individual mistakes identified.</p>
                  )}
                </div>
              )}

              {activeTab === 'vision' && (
                <div className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="glass-panel p-4 rounded-xl border-l-2 border-blue-400">
                      <p className="text-[10px] font-bold text-slate-500 uppercase">
                        {currentData?.game === 'valorant' ? 'Blue Round Econ' : 'Blue Vision Score'}
                      </p>
                      <p className="text-2xl font-black italic">{currentData?.game === 'valorant' ? '3,400' : '142'}</p>
                      <p className="text-[10px] text-green-400 font-bold uppercase mt-1">
                        {currentData?.game === 'valorant' ? 'Full Buy' : '+12% vs League Avg'}
                      </p>
                    </div>
                    <div className="glass-panel p-4 rounded-xl border-l-2 border-red-400">
                      <p className="text-[10px] font-bold text-slate-500 uppercase">
                        {currentData?.game === 'valorant' ? 'Red Round Econ' : 'Red Vision Score'}
                      </p>
                      <p className="text-2xl font-black italic">{currentData?.game === 'valorant' ? '1,200' : '118'}</p>
                      <p className="text-[10px] text-red-400 font-bold uppercase mt-1">
                        {currentData?.game === 'valorant' ? 'Eco Round' : '-5% vs League Avg'}
                      </p>
                    </div>
                    <div className="glass-panel p-4 rounded-xl border-l-2 border-primary">
                      <p className="text-[10px] font-bold text-slate-500 uppercase">
                        {currentData?.game === 'valorant' ? 'Econ Efficiency' : 'Vision Denial Rate'}
                      </p>
                      <p className="text-2xl font-black italic">{currentData?.game === 'valorant' ? '82%' : '64%'}</p>
                      <p className="text-[10px] text-primary font-bold uppercase mt-1">
                        {currentData?.game === 'valorant' ? 'Optimal Spend' : 'Excellent Control'}
                      </p>
                    </div>
                  </div>
                  
                  <div className="p-6 rounded-2xl bg-slate-900/40 border border-slate-800">
                    <h3 className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-6">
                      {currentData?.game === 'valorant' ? 'Economy Advantage Timeline' : 'Warding Activity Timeline'}
                    </h3>
                    <div className="h-[200px] w-full">
                      <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={chartData}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                          <XAxis dataKey="time" stroke="#475569" fontSize={10} />
                          <YAxis stroke="#475569" fontSize={10} />
                          <Tooltip contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b' }} />
                          <Area type="monotone" dataKey="goldDiff" name={data?.game === 'valorant' ? 'Econ Delta' : 'Vision Control Index'} stroke="#00a3ff" fill="#00a3ff" fillOpacity={0.1} />
                        </AreaChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
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
                          <th className="pb-4 text-right">{data?.game === 'valorant' ? 'ACS' : 'GPM'}</th>
                          <th className="pb-4 text-right">{data?.game === 'valorant' ? 'ADR' : 'Gold'}</th>
                          <th className="pb-4 text-right">{data?.game === 'valorant' ? 'Credits' : 'Total CS'}</th>
                          <th className="pb-4 text-right">{data?.game === 'valorant' ? 'HS %' : 'CS/M'}</th>
                          <th className="pb-4 text-right">Efficiency</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800">
                        {currentData?.player_stats?.map((p: any) => (
                          <tr 
                            key={p.player_id} 
                            onClick={() => setSelectedPlayer(p.player_id)}
                            className={`group hover:bg-slate-900/50 transition-colors cursor-pointer ${selectedPlayer === p.player_id ? 'bg-primary/5 border-l-2 border-primary' : ''}`}
                          >
                            <td className="py-4 font-bold text-sm pl-2">Player {p.player_id}</td>
                            <td className="py-4 text-xs uppercase font-bold">
                              <span className={(p.team_id === 100 || p.team_id === 'team-blue') ? 'text-blue-500' : 'text-red-500'}>
                                {(p.team_id === 100 || p.team_id === 'team-blue') ? 'Blue' : 'Red'}
                              </span>
                            </td>
                            <td className="py-4 text-right font-mono text-sm">
                              {currentData?.game === 'valorant' ? p.acs?.toFixed(0) : p.gpm?.toFixed(0)}
                            </td>
                            <td className="py-4 text-right font-mono text-sm">
                              {currentData?.game === 'valorant' ? p.adr?.toFixed(0) : p.total_gold?.toLocaleString()}
                            </td>
                            <td className="py-4 text-right font-mono text-sm">
                              {currentData?.game === 'valorant' ? p.credits?.toLocaleString() : p.total_cs || 0}
                            </td>
                            <td className="py-4 text-right font-mono text-sm">
                              {currentData?.game === 'valorant' ? `${p.headshot_percent?.toFixed(1)}%` : p.cs_per_min?.toFixed(1) || '0.0'}
                            </td>
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
                            { 
                              subject: currentData?.game === 'valorant' ? 'ACS' : 'GPM', 
                              A: currentData?.game === 'valorant' ? currentData?.player_stats?.find((p:any) => p.player_id === selectedPlayer)?.acs / 3 : currentData?.player_stats?.find((p:any) => p.player_id === selectedPlayer)?.gpm / 10, 
                              fullMark: 100 
                            },
                            { 
                              subject: 'KP%', 
                              A: currentData?.player_stats?.find((p:any) => p.player_id === selectedPlayer)?.kill_participation, 
                              fullMark: 100 
                            },
                            { 
                              subject: currentData?.game === 'valorant' ? 'HS%' : 'Vision', 
                              A: currentData?.game === 'valorant' ? currentData?.player_stats?.find((p:any) => p.player_id === selectedPlayer)?.headshot_percent * 2 : currentData?.player_stats?.find((p:any) => p.player_id === selectedPlayer)?.vision_score * 2, 
                              fullMark: 100 
                            },
                            { 
                              subject: currentData?.game === 'valorant' ? 'ADR' : 'Damage', 
                              A: currentData?.game === 'valorant' ? currentData?.player_stats?.find((p:any) => p.player_id === selectedPlayer)?.adr / 2 : currentData?.player_stats?.find((p:any) => p.player_id === selectedPlayer)?.damage_share * 4, 
                              fullMark: 100 
                            },
                            { 
                              subject: 'Efficiency', 
                              A: currentData?.player_stats?.find((p:any) => p.player_id === selectedPlayer)?.efficiency_score, 
                              fullMark: 100 
                            },
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
                          <p className="text-[10px] text-slate-500 uppercase font-bold">{currentData?.game === 'valorant' ? 'Headshot %' : 'Vision Score'}</p>
                          <p className="text-lg font-black text-primary italic">
                            {currentData?.game === 'valorant' 
                              ? `${currentData?.player_stats?.find((p:any) => p.player_id === selectedPlayer)?.headshot_percent?.toFixed(1)}%` 
                              : currentData?.player_stats?.find((p:any) => p.player_id === selectedPlayer)?.vision_score}
                          </p>
                        </div>
                        <div className="p-3 bg-slate-800/40 rounded-lg">
                          <p className="text-[10px] text-slate-500 uppercase font-bold">KP %</p>
                          <p className="text-lg font-black text-primary italic">{currentData?.player_stats?.find((p:any) => p.player_id === selectedPlayer)?.kill_participation}%</p>
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

              {activeTab === 'draft' && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                  {data?.metadata?.teams?.map((team: any, i: number) => (
                    <div key={i} className="glass-panel p-6 rounded-2xl border-t-4 border-t-primary">
                      <div className="flex justify-between items-center mb-6">
                        <h3 className="text-xl font-black italic">{team.name}</h3>
                        <span className={`text-[10px] font-bold px-3 py-1 rounded-full uppercase ${team.side === 'blue' ? 'bg-blue-500/20 text-blue-500' : 'bg-red-500/20 text-red-500'}`}>
                          {team.side} Side
                        </span>
                      </div>
                      
                      <div className="space-y-3">
                        {team.draft?.map((champ: string, idx: number) => (
                          <div key={idx} className="flex items-center gap-4 p-3 bg-slate-900/50 rounded-xl border border-slate-800">
                             <div className="w-10 h-10 rounded-lg bg-slate-800 flex items-center justify-center font-black text-slate-500">
                               {champ[0]}
                             </div>
                             <div className="flex-1">
                               <p className="font-bold text-sm">{champ}</p>
                               <p className="text-[10px] text-slate-500 uppercase">
                                 {data?.game === 'valorant' 
                                   ? ['DUELIST', 'CONTROLLER', 'SENTINEL', 'INITIATOR', 'CONTROLLER'][idx % 5]
                                   : ['TOP', 'JNG', 'MID', 'ADC', 'SUP'][idx % 5]}
                               </p>
                             </div>
                             <ChevronRight className="w-4 h-4 text-slate-700" />
                          </div>
                        ))}
                      </div>

                      <div className="mt-8 pt-6 border-t border-slate-800">
                        <div className="flex justify-between mb-2">
                           <span className="text-[10px] font-bold text-slate-500 uppercase">Synergy Score</span>
                           <span className="text-primary font-black italic">{data?.draft_analysis?.[team.id]?.synergy_score}%</span>
                        </div>
                        <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                          <div className="h-full bg-primary" style={{ width: `${data?.draft_analysis?.[team.id]?.synergy_score}%` }} />
                        </div>
                        <p className="text-[10px] text-slate-400 mt-4 italic">
                          "This draft favors {data?.draft_analysis?.[team.id]?.power_spike} engagements with strong scaling."
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {activeTab === 'map' && (
                <div className="flex flex-col items-center gap-8 py-8">
                   <div className="relative w-full max-w-[600px] aspect-square bg-[#0a1120] border-2 border-primary/30 rounded-[2rem] overflow-hidden shadow-[0_0_50px_rgba(0,163,255,0.15)] group">
                      {/* Radar/Scanning effect */}
                      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(0,163,255,0.05)_0%,transparent_70%)]" />
                      
                      {/* Simplified Rift Grid */}
                      <div className="absolute inset-0 opacity-20 pointer-events-none">
                         <div className="absolute top-0 left-0 w-full h-full border-b border-r border-primary/20" />
                         <div className="absolute top-1/2 left-0 w-full h-0.5 bg-primary/20" />
                         <div className="absolute top-0 left-1/2 w-0.5 h-full bg-primary/20" />
                         <div className="absolute top-0 left-0 w-full h-full border-[1px] border-primary/10 rounded-full scale-75" />
                         <div className="absolute top-0 left-0 w-full h-full border-[1px] border-primary/10 rounded-full scale-50" />
                      </div>

                      {/* Players */}
                      {currentData?.current_snapshot?.participantFrames && 
                        Object.entries(currentData.current_snapshot.participantFrames).map(([pid, frame]: any) => {
                          const scale = currentData?.game === 'valorant' ? 12000 : 15000;
                          const x = (frame.position?.x || 0) / scale * 100;
                          const y = 100 - ((frame.position?.y || 0) / scale * 100);
                          const isBlue = currentData?.game === 'valorant' ? (parseInt(pid) <= 5) : (parseInt(pid) <= 5);
                          return (
                            <motion.div
                              key={pid}
                              initial={false}
                              transition={{ type: "spring", stiffness: 300, damping: 30 }}
                              animate={{ left: `${x}%`, top: `${y}%` }}
                              className="absolute w-6 h-6 -translate-x-1/2 -translate-y-1/2 flex items-center justify-center z-20"
                            >
                              <div className={cn(
                                "w-full h-full rounded-full border-2 border-white/80 shadow-[0_0_15px_rgba(255,255,255,0.3)] flex items-center justify-center text-[10px] font-black",
                                isBlue ? 'bg-blue-600' : 'bg-red-600'
                              )}>
                                {pid}
                              </div>
                              <div className={cn(
                                "absolute inset-[-4px] rounded-full border border-dashed opacity-50 animate-spin-slow",
                                isBlue ? 'border-blue-400' : 'border-red-400'
                              )} style={{ animationDuration: '4s' }} />
                            </motion.div>
                          );
                        })
                      }
                      
                      {/* Base Markers */}
                      <div className="absolute bottom-6 left-6 w-12 h-12 bg-blue-500/10 border-2 border-blue-500/50 rounded-xl animate-pulse flex items-center justify-center">
                        <Shield className="text-blue-500/50 w-6 h-6" />
                      </div>
                      <div className="absolute top-6 right-6 w-12 h-12 bg-red-500/10 border-2 border-red-500/50 rounded-xl animate-pulse flex items-center justify-center">
                        <Shield className="text-red-500/50 w-6 h-6" />
                      </div>

                      <div className="absolute bottom-4 right-4 bg-black/60 backdrop-blur-md px-3 py-1 rounded-full border border-primary/30 text-[8px] font-mono text-primary animate-pulse">
                        SENSORS ACTIVE // SECTOR 7G
                      </div>
                   </div>
                   <div className="text-center">
                      <p className="text-sm font-black text-slate-100 uppercase tracking-[0.4em] italic">Tactical Rift Overlay</p>
                      <p className="text-[10px] text-primary font-mono mt-2 uppercase opacity-50">Syncing positioning telemetry via GRID Neural Link...</p>
                   </div>
                </div>
              )}

                  {activeTab === 'what-if' && (
                <div className="space-y-6">
                  <div className="p-8 rounded-3xl border-2 border-dashed border-primary/20 bg-primary/5 text-center relative overflow-hidden group">
                    <div className="absolute inset-0 bg-primary/5 opacity-0 group-hover:opacity-100 transition-opacity animate-pulse pointer-events-none" />
                    <BrainCircuit className="w-12 h-12 text-primary mx-auto mb-4" />
                    <h3 className="text-2xl font-black italic uppercase tracking-tighter text-white">Neural Simulation Engine</h3>
                    <p className="text-sm text-slate-400 max-w-md mx-auto mt-2 font-medium">Quantify tactical decisions by injecting counterfactual game states into the XGBoost model.</p>
                    
                    {!isSimulated && (
                      <div className="flex justify-center gap-4 mt-8">
                        <button 
                          onClick={() => handleSimulate({})}
                          disabled={isSimulating}
                          className="group flex items-center gap-4 px-12 py-5 bg-primary text-black font-black uppercase italic rounded-full shadow-[0_0_40px_rgba(0,163,255,0.4)] hover:scale-105 active:scale-95 transition-all duration-300 disabled:opacity-50"
                        >
                          {isSimulating ? 'Initializing...' : 'RUN LIVE SIMULATION'}
                          <RefreshCcw className={`w-6 h-6 ${isSimulating ? 'animate-spin' : ''}`} />
                        </button>
                      </div>
                    )}
                  </div>

                  {isSimulated && (
                    <motion.div 
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="p-8 rounded-3xl bg-slate-900/80 border border-primary/30 shadow-[0_0_50px_rgba(0,163,255,0.1)] flex flex-col items-stretch gap-8 relative"
                    >
                       <div className="absolute top-4 right-4">
                          <button onClick={() => setIsSimulated(false)} className="text-[10px] font-black text-slate-500 uppercase hover:text-red-500 transition-colors">TERMINATE SESSION [X]</button>
                       </div>

                       <div className="flex flex-col md:flex-row items-center justify-between gap-8">
                        <div className="flex items-center gap-6">
                          <div className="bg-primary/20 p-5 rounded-2xl shadow-[0_0_20px_rgba(0,163,255,0.3)] border border-primary/30">
                            <Activity className="text-primary w-10 h-10 animate-pulse"/>
                          </div>
                          <div>
                            <p className="text-xs font-bold text-primary uppercase tracking-[0.3em] mb-1">Projected Outcome</p>
                            <p className="text-5xl font-black italic text-white tracking-tighter">
                              {((simulationResult?.win_probability || 0) * 100).toFixed(1)}%
                            </p>
                          </div>
                        </div>
                        
                        <div className="flex gap-10 items-center bg-black/40 p-6 rounded-2xl border border-slate-800">
                          <div className="text-center">
                            <p className="text-[10px] text-slate-500 font-black uppercase mb-1">Probability Delta</p>
                            <p className={`text-3xl font-black italic ${ (simulationResult?.win_probability - (data?.timeline_snapshots?.[data.timeline_snapshots.length - 1]?.win_prob || 0.5)) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                              {(simulationResult?.win_probability - (data?.timeline_snapshots?.[data.timeline_snapshots.length - 1]?.win_prob || 0.5)) >= 0 ? '+' : ''}
                              {((simulationResult?.win_probability - (data?.timeline_snapshots?.[data.timeline_snapshots.length - 1]?.win_prob || 0.5)) * 100).toFixed(1)}%
                            </p>
                          </div>
                          <div className="w-[1px] h-12 bg-slate-800" />
                          <div className="text-center">
                            <p className="text-[10px] text-slate-500 font-black uppercase mb-1">Confidence Rating</p>
                            <p className="text-3xl font-mono font-bold text-slate-100">98.2%</p>
                          </div>
                        </div>
                      </div>

                      {simulationResult?.explanation && (
                        <div className="p-4 bg-primary/10 border border-primary/30 rounded-xl relative overflow-hidden">
                           <div className="absolute top-0 left-0 w-1 h-full bg-primary" />
                           <p className="text-[10px] font-black text-primary uppercase mb-2 flex items-center gap-2">
                             <BrainCircuit className="w-3 h-3" />
                             XAI Neural Analysis
                           </p>
                           <p className="text-sm text-slate-300 italic">"{simulationResult.explanation}"</p>
                        </div>
                      )}

                      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 pt-8 border-t border-slate-800">
                        <div className="space-y-4">
                          <div className="flex justify-between">
                            <p className="text-[10px] text-slate-400 uppercase font-black tracking-widest">Economy Injector</p>
                            <p className="text-xs font-mono text-primary">{simulationResult?.modified_state?.gold_diff || data?.current_state?.gold_diff}</p>
                          </div>
                          <input 
                            type="range" min="-20000" max="20000" step="500"
                            value={simulationResult?.modified_state?.gold_diff || data?.current_state?.gold_diff}
                            onChange={(e) => handleSimulate({ gold_diff: parseInt(e.target.value) })}
                            className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-primary shadow-[0_0_10px_rgba(0,163,255,0.2)]"
                          />
                        </div>
                        <div className="space-y-4">
                          <p className="text-[10px] text-slate-400 uppercase font-black tracking-widest">Objective Control</p>
                          <div className="flex gap-2">
                             {[0, 1, 2, 3, 4].map(val => (
                               <button 
                                key={val}
                                onClick={() => handleSimulate({ dragons_diff: val })}
                                className={cn(
                                  "flex-1 py-2 rounded-lg text-xs font-black transition-all",
                                  (simulationResult?.modified_state?.dragons_diff ?? data?.current_state?.dragons_diff) === val 
                                    ? 'bg-primary text-black shadow-[0_0_15px_rgba(0,163,255,0.4)]' 
                                    : 'bg-slate-800 text-slate-500 hover:bg-slate-700'
                                )}
                               >
                                 {val}
                               </button>
                             ))}
                          </div>
                        </div>
                        <div className="space-y-4">
                          <p className="text-[10px] text-slate-400 uppercase font-black tracking-widest">Structure Denial</p>
                          <div className="flex gap-2">
                             {[0, 2, 5, 8, 11].map(val => (
                               <button 
                                key={val}
                                onClick={() => handleSimulate({ towers_diff: val })}
                                className={cn(
                                  "flex-1 py-2 rounded-lg text-xs font-black transition-all",
                                  (simulationResult?.modified_state?.towers_diff ?? data?.current_state?.towers_diff) === val 
                                    ? 'bg-primary text-black shadow-[0_0_15px_rgba(0,163,255,0.4)]' 
                                    : 'bg-slate-800 text-slate-500 hover:bg-slate-700'
                                )}
                               >
                                 {val}
                               </button>
                             ))}
                          </div>
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
              {`COACH'S INTELLIGENCE`}
            </h2>
            
            <div className="space-y-6 flex-1 overflow-auto pr-2 custom-scrollbar">
              <div className="bg-slate-900/80 p-5 rounded-xl border border-slate-800 relative shadow-[0_0_15px_rgba(0,0,0,0.5)]">
                <div className="absolute -top-2 -left-2 bg-primary text-white text-[10px] font-black text-6xl px-2 py-4 italic shadow-[0_0_10px_rgba(0,163,255,0.5)] w-full ml-2 rounded-md mt-2">NEURAL SUMMARY</div>
                <div className="text-sm leading-relaxed text-slate-300 prose prose-invert prose-sm max-w-none mt-10">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {data?.ai_coach_summary}
                  </ReactMarkdown>
                </div>
              </div>

              {/* SHAP Feature Importance */}
              <div className="bg-slate-900/40 p-5 rounded-xl border border-slate-800">
                <h3 className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em] mb-4 flex items-center gap-2">
                  <Activity className="w-3 h-3 text-primary" />
                  Decision Drivers (SHAP)
                </h3>
                <div className="h-[200px] w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={shapData} layout="vertical" margin={{ left: -20 }}>
                      <XAxis type="number" hide />
                      <YAxis dataKey="name" type="category" stroke="#475569" fontSize={8} width={80} />
                      <Tooltip 
                        cursor={{ fill: 'transparent' }}
                        contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b' }}
                      />
                      <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                        {shapData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.value > 0 ? '#22c55e' : '#ef4444'} fillOpacity={0.6} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                <p className="text-[8px] text-slate-600 font-mono mt-2 italic text-center uppercase tracking-tighter">Impact on Win Probability %</p>
              </div>

              <div className="space-y-4">
                <h3 className="text-[10px] font-bold text-slate-500 uppercase tracking-[0.2em]">Priority Action Items</h3>
                {(currentData?.micro_insights && currentData.micro_insights.length > 0) ? (
                  currentData.micro_insights.slice(0, 3).map((item: any, i: number) => (
                    <div key={i} className="flex gap-3 items-center p-3 rounded-lg bg-slate-900/30 border border-slate-800/50 hover:border-primary/50 transition-colors group cursor-pointer">
                      <div className="text-primary group-hover:scale-110 transition-transform">
                        {item.type.includes('Death') ? <Shield className="w-4 h-4" /> : <Zap className="w-4 h-4" />}
                      </div>
                      <p className="text-sm font-medium">{item.details}</p>
                      <ChevronRight className="w-4 h-4 text-slate-700 ml-auto group-hover:text-primary transition-colors" />
                    </div>
                  ))
                ) : (
                  [
                    { icon: <Shield className="w-4 h-4" />, text: 'Address isolated deaths detected' },
                    { icon: <Zap className="w-4 h-4" />, text: 'Optimize Dragon setup rotations' },
                    { icon: <Target className="w-4 h-4" />, text: 'Review mid-game gold lead erosion' }
                  ].map((item, i) => (
                    <div key={i} className="flex gap-3 items-center p-3 rounded-lg bg-slate-900/30 border border-slate-800/50 hover:border-primary/50 transition-colors group cursor-pointer">
                      <div className="text-primary group-hover:scale-110 transition-transform">{item.icon}</div>
                      <p className="text-sm font-medium">{item.text}</p>
                      <ChevronRight className="w-4 h-4 text-slate-700 ml-auto group-hover:text-primary transition-colors" />
                    </div>
                  ))
                )}
              </div>
            </div>

            <div className="pt-6 mt-auto border-t border-slate-800">
               <button 
                onClick={() => window.print()}
                className="w-full py-4 glass-panel border border-primary/30 text-primary text-[10px] font-black uppercase tracking-[0.3em] hover:bg-primary/10 transition-colors flex items-center justify-center gap-2 shadow-[0_0_20px_rgba(0,163,255,0.1)]"
               >
                 EXPORT MATCH REVIEW PDF
                 <Maximize2 className="w-4 h-4" />
               </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
