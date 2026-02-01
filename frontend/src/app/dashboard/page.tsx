'use client';

import React, { useState, useEffect } from 'react';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area 
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
  Maximize2
} from 'lucide-react';
import { motion } from 'framer-motion';

const MOCK_CHART_DATA = [
  { time: '0:00', prob: 0.50 },
  { time: '5:00', prob: 0.52 },
  { time: '10:00', prob: 0.48 },
  { time: '15:00', prob: 0.55 },
  { time: '20:00', prob: 0.35 }, // Significant drop
  { time: '25:00', prob: 0.42 },
  { time: '30:00', prob: 0.45 },
];

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState('macro');
  const [isSimulated, setIsSimulated] = useState(false);

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
        <div className="flex gap-4">
          <div className="text-right">
            <p className="text-xs text-slate-500 uppercase font-bold">Live Match Analysis</p>
            <p className="text-sm font-mono text-primary animate-pulse">C9 vs T1 - Match #4028</p>
          </div>
          <div className="h-10 w-10 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center">
            <div className="h-2 w-2 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.8)]" />
          </div>
        </div>
      </header>

      <main className="grid grid-cols-12 gap-6">
        {/* Left Column: Stats & Chart */}
        <div className="col-span-12 lg:col-span-8 space-y-6">
          {/* Main Visualizer */}
          <div className="glass-panel p-6 rounded-2xl relative overflow-hidden">
            <div className="absolute top-0 left-0 w-1 h-full bg-primary" />
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-lg font-bold flex items-center gap-2">
                <BarChart3 className="text-primary w-5 h-5" />
                WIN PROBABILITY TELEMETRY
              </h2>
              <div className="flex gap-2">
                <span className="px-3 py-1 bg-red-500/10 text-red-500 border border-red-500/20 rounded text-[10px] font-bold">HIGH VOLATILITY</span>
                <span className="px-3 py-1 bg-slate-800 text-slate-400 rounded text-[10px] font-bold uppercase">Live Snapshot</span>
              </div>
            </div>
            
            <div className="h-[300px] w-full mt-4">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={MOCK_CHART_DATA}>
                  <defs>
                    <linearGradient id="colorProb" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#00a3ff" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#00a3ff" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                  <XAxis dataKey="time" stroke="#475569" fontSize={12} tickLine={false} axisLine={false} />
                  <YAxis domain={[0, 1]} stroke="#475569" fontSize={12} tickLine={false} axisLine={false} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '8px' }}
                    itemStyle={{ color: '#00a3ff' }}
                  />
                  <Area type="monotone" dataKey="prob" stroke="#00a3ff" strokeWidth={3} fillOpacity={1} fill="url(#colorProb)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Bottom Grid: Insights Tabs */}
          <div className="glass-panel rounded-2xl p-1">
            <div className="flex border-b border-blue-900/50">
              {['macro', 'micro', 'what-if'].map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`px-6 py-4 text-sm font-bold uppercase tracking-wider transition-all ${
                    activeTab === tab 
                    ? 'text-primary border-b-2 border-primary' 
                    : 'text-slate-500 hover:text-slate-300'
                  }`}
                >
                  {tab} Review
                </button>
              ))}
            </div>
            
            <div className="p-6">
              {activeTab === 'macro' && (
                <div className="space-y-4">
                  <div className="flex items-start gap-4 p-4 rounded-xl bg-slate-900/50 border border-slate-800">
                    <div className="bg-yellow-500/20 p-2 rounded-lg"><AlertTriangle className="text-yellow-500 w-5 h-5"/></div>
                    <div>
                      <h4 className="font-bold text-slate-100">OBJECTIVE GAP: DRAGON PIT (15:42)</h4>
                      <p className="text-sm text-slate-400 mt-1">Foundational error in vision setup. C9 gave up mid-control 45s prior to spawn, leading to a 12% probability drop.</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-4 p-4 rounded-xl bg-slate-900/50 border border-slate-800">
                    <div className="bg-blue-500/20 p-2 rounded-lg"><TrendingUp className="text-blue-500 w-5 h-5"/></div>
                    <div>
                      <h4 className="font-bold text-slate-100">GOLD PEAK: TOP TOWER (22:10)</h4>
                      <p className="text-sm text-slate-400 mt-1">Excellent macro rotation. Capitalized on T1's over-extension in bot lane. Net gain: +1,200g.</p>
                    </div>
                  </div>
                </div>
              )}
              
              {activeTab === 'micro' && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {[
                    { p: 'Berserker', m: 'Missed base timer (-300g effective)', t: 'Critical' },
                    { p: 'Jojo', m: 'Isolated death in river', t: 'Severe' },
                    { p: 'Blaber', m: 'Pathing leaked by ward', t: 'Moderate' }
                  ].map((mistake, i) => (
                    <div key={i} className="p-4 rounded-xl bg-slate-900/50 border border-slate-800 flex justify-between items-center">
                      <div className="flex gap-3 items-center">
                        <div className="w-8 h-8 rounded bg-primary/10 flex items-center justify-center font-bold text-primary text-xs">C9</div>
                        <div>
                          <p className="text-xs font-bold text-slate-500 uppercase">{mistake.p}</p>
                          <p className="text-sm font-medium">{mistake.m}</p>
                        </div>
                      </div>
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase ${
                        mistake.t === 'Critical' ? 'bg-red-500/20 text-red-500' : 'bg-slate-700 text-slate-300'
                      }`}>
                        {mistake.t}
                      </span>
                    </div>
                  ))}
                </div>
              )}

              {activeTab === 'what-if' && (
                <div className="space-y-6">
                  <div className="p-6 rounded-2xl border-2 border-dashed border-primary/30 bg-primary/5 text-center">
                    <BrainCircuit className="w-10 h-10 text-primary mx-auto mb-4" />
                    <h3 className="text-xl font-bold italic">DECISION CRUNCHER</h3>
                    <p className="text-sm text-slate-400 max-w-md mx-auto mt-2">Modify the game state to see how win probability shifts based on alternative macro choices.</p>
                    
                    <div className="flex justify-center gap-4 mt-8">
                      <button 
                         onClick={() => setIsSimulated(!isSimulated)}
                         className="px-8 py-3 bg-primary text-black font-black uppercase italic rounded-full shadow-[0_0_20px_rgba(0,163,255,0.4)] hover:scale-105 transition-transform"
                      >
                        {isSimulated ? 'RESET STATE' : 'RUN SIMULATION'}
                      </button>
                    </div>
                  </div>

                  {isSimulated && (
                    <motion.div 
                      initial={{ opacity: 0, scale: 0.95 }}
                      animate={{ opacity: 1, scale: 1 }}
                      className="p-4 rounded-xl bg-green-500/10 border border-green-500/30 flex items-center justify-between"
                    >
                      <div className="flex items-center gap-4">
                        <div className="bg-green-500/20 p-3 rounded-full"><Target className="text-green-500 w-6 h-6"/></div>
                        <div>
                          <p className="text-xs font-bold text-green-500 uppercase">What If: Contested 3rd Dragon</p>
                          <p className="text-lg font-black italic">+18.4% WIN PROBABILITY</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-xs text-slate-500 font-bold uppercase">Confidence</p>
                        <p className="text-lg font-mono font-bold">87.2%</p>
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
          <div className="glass-panel p-6 rounded-2xl h-full border-r border-primary/30">
            <h2 className="text-lg font-bold flex items-center gap-2 mb-6">
              <BrainCircuit className="text-primary w-5 h-5" />
              AI ASSISTANT COACH
            </h2>
            
            <div className="space-y-6">
              <div className="bg-slate-900/80 p-5 rounded-xl border border-slate-800 relative">
                <div className="absolute -top-2 -left-2 bg-primary text-black text-[10px] font-black px-2 py-0.5 italic">SUMMARY</div>
                <p className="text-sm leading-relaxed text-slate-300">
                  Overall match performance was <span className="text-primary font-bold">Stable</span> but lacked <span className="text-primary font-bold">Aggressive Macro</span>. 
                  Individual errors from Berserker and Jojo at minute 15 and 22 resulted in a net gold loss of 2,400g.
                </p>
              </div>

              <div className="space-y-4">
                <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest">Action Items</h3>
                {[
                  { icon: <Shield className="w-4 h-4" />, text: 'Improve bot-lane jungle proximity' },
                  { icon: <Zap className="w-4 h-4" />, text: 'Prioritize Baron vision at 20:00' },
                  { icon: <Target className="w-4 h-4" />, text: 'Review Berserker base timings' }
                ].map((item, i) => (
                  <div key={i} className="flex gap-3 items-center p-3 rounded-lg bg-slate-900/30 border border-slate-800/50 hover:border-primary/50 transition-colors">
                    <div className="text-primary">{item.icon}</div>
                    <p className="text-sm font-medium">{item.text}</p>
                  </div>
                ))}
              </div>

              <div className="pt-6 border-t border-slate-800">
                 <button className="w-full py-4 glass-panel border border-primary/30 text-primary text-xs font-black uppercase tracking-widest hover:bg-primary/10 transition-colors flex items-center justify-center gap-2">
                   EXPAND MATCH LOGS
                   <Maximize2 className="w-4 h-4" />
                 </button>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
