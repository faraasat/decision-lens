import Link from 'next/link';
import { Cpu, ChevronRight } from 'lucide-react';

export default function Home() {
  return (
    <div className="min-h-screen bg-[#050a14] cyber-grid flex flex-col items-center justify-center p-6 text-center">
      <div className="glass-panel p-12 rounded-3xl max-w-2xl border-2 border-primary/20 relative">
        <div className="absolute -top-10 left-1/2 -translate-x-1/2 bg-[#050a14] p-4 rounded-full border border-primary/30">
          <Cpu className="w-12 h-12 text-primary animate-pulse" />
        </div>
        
        <h1 className="text-6xl font-black tracking-tighter italic mb-4">
          DECISION<span className="text-primary italic">LENS</span>
        </h1>
        <p className="text-xl text-slate-400 font-medium mb-12 uppercase tracking-[0.2em]">
          AI Assistant Coach for League of Legends
        </p>

        <div className="grid grid-cols-3 gap-6 mb-12 text-slate-100">
          <div className="space-y-2">
            <p className="text-3xl font-black text-primary italic">98%</p>
            <p className="text-[10px] font-bold text-slate-500 uppercase">Analysis Precision</p>
          </div>
          <div className="space-y-2 border-x border-slate-800">
            <p className="text-3xl font-black text-primary italic">Real</p>
            <p className="text-[10px] font-bold text-slate-500 uppercase">Time Telemetry</p>
          </div>
          <div className="space-y-2">
            <p className="text-3xl font-black text-primary italic">XGB</p>
            <p className="text-[10px] font-bold text-slate-500 uppercase">Decision Engine</p>
          </div>
        </div>

        <Link 
          href="/dashboard"
          className="group inline-flex items-center gap-3 px-10 py-5 bg-primary text-black font-black uppercase italic rounded-full shadow-[0_0_30px_rgba(0,163,255,0.4)] hover:scale-105 transition-all duration-300"
        >
          Initialize Coach System
          <ChevronRight className="w-6 h-6 group-hover:translate-x-1 transition-transform" />
        </Link>
      </div>

      <footer className="mt-12">
        <p className="text-[10px] font-bold text-slate-600 uppercase tracking-widest text-slate-500">
          Powering Cloud9 Decision Intelligence // Hackathon Submission 2026
        </p>
      </footer>
    </div>
  );
}
