
import React, { useState } from "react";

export default function FitMindApp() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [email, setEmail] = useState("sarah@yourgym.com");
  const [password, setPassword] = useState("••••••••");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    // Simulate login authentication flow
    setTimeout(() => {
      if (email && password) {
        setIsLoggedIn(true);
      } else {
        setError("Please provide a valid email and password.");
      }
      setLoading(false);
    }, 800);
  };

  const handleLogout = () => {
    setIsLoggedIn(false);
  };

  // ============================================================
  // 1. LOGIN SCREEN VIEW
  // ============================================================
  if (!isLoggedIn) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#0f0f1a] via-[#1a1a3e] to-[#2d1b4e] p-4 font-sans text-white">
        <div className="w-full max-w-md p-8 rounded-2xl bg-[#1e1e3f] border border-[#2d2d44] shadow-2xl">
          <div className="text-center mb-8">
            <div className="text-5xl mb-3">🏋️</div>
            <h1 className="text-3xl font-black text-white tracking-tight">FitMind AI</h1>
            <p className="text-[#94a3b8] mt-2 text-sm font-medium">The AI that runs your gym</p>
          </div>

          <form onSubmit={handleLogin} className="space-y-5">
            <div>
              <label className="block text-sm font-semibold text-[#94a3b8] mb-2">
                Email
              </label>
              <input
                name="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full px-4 py-3 rounded-xl bg-[#0a0a14] border border-[#2d2d44] text-white 
                           placeholder-[#475569] focus:outline-none focus:border-[#6366f1] focus:ring-1 
                           focus:ring-[#6366f1] transition-all text-sm"
                placeholder="sarah@yourgym.com"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-[#94a3b8] mb-2">
                Password
              </label>
              <input
                name="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full px-4 py-3 rounded-xl bg-[#0a0a14] border border-[#2d2d44] text-white 
                           placeholder-[#475569] focus:outline-none focus:border-[#6366f1] focus:ring-1 
                           focus:ring-[#6366f1] transition-all text-sm"
                placeholder="••••••••"
              />
            </div>

            {error && (
              <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3.5 rounded-xl bg-gradient-to-r from-[#6366f1] to-[#8b5cf6] 
                         text-white font-bold text-sm hover:opacity-90 transition-opacity 
                         disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-indigo-500/20"
            >
              {loading ? "Signing in..." : "Sign In to Dashboard"}
            </button>
          </form>

          <p className="text-center text-xs text-[#475569] mt-6">
            Don't have an account?{" "}
            <a href="#" onClick={(e) => { e.preventDefault(); setIsLoggedIn(true); }} className="text-[#6366f1] hover:text-[#818cf8] font-semibold">
              Start free trial
            </a>
          </p>
        </div>
      </div>
    );
  }

  // ============================================================
  // 2. MAIN GYM OS DASHBOARD VIEW
  // ============================================================
  return (
    <div className="min-h-screen bg-[#0a0a14] font-sans text-slate-100">
      {/* HEADER */}
      <header className="bg-gradient-to-r from-[#0f0f1a] to-[#1a1a3e] border-b border-[#1e1e3f] px-6 md:px-8 py-5">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <div className="text-xs font-bold text-[#818cf8] uppercase tracking-widest mb-1">
              AI-Powered Gym OS
            </div>
            <h1 className="text-2xl font-black text-white flex items-center gap-2">
              🏋️ FitMind AI
            </h1>
          </div>

          <div className="flex items-center gap-4">
            <span className="px-4 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-bold flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              All Systems Online
            </span>

            <div className="flex items-center gap-3 border-l border-[#2d2d44] pl-4">
              <div className="text-right hidden sm:block">
                <div className="text-sm font-bold text-white">Sarah Jenkins</div>
                <div className="text-xs text-[#64748b]">Metro Fitness Club</div>
              </div>
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[#6366f1] to-[#ec4899] flex items-center justify-center text-white font-bold shadow-md">
                S
              </div>
              <button
                onClick={handleLogout}
                className="text-xs text-slate-400 hover:text-white bg-[#1e1e3f] border border-[#2d2d44] px-3 py-1.5 rounded-lg transition"
              >
                Sign Out
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* MAIN DASHBOARD CONTENT */}
      <main className="p-6 md:p-8 max-w-7xl mx-auto space-y-6">
        
        {/* KPI CARDS GRID */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          <div className="bg-gradient-to-br from-[#1e1e3f] to-[#161632] rounded-2xl p-5 border border-[#2d2d44] hover:border-[#3d3d5c] transition-all">
            <div className="flex justify-between items-center mb-2">
              <span className="text-xs font-bold text-[#64748b] uppercase tracking-wider">Active Members</span>
              <span>👥</span>
            </div>
            <div className="text-3xl font-black text-emerald-400">1,248</div>
            <div className="text-xs mt-1 font-semibold text-emerald-400/80">↑ 12% vs last month</div>
          </div>

          <div className="bg-gradient-to-br from-[#1e1e3f] to-[#161632] rounded-2xl p-5 border border-[#2d2d44] hover:border-[#3d3d5c] transition-all">
            <div className="flex justify-between items-center mb-2">
              <span className="text-xs font-bold text-[#64748b] uppercase tracking-wider">MRR Revenue</span>
              <span>💰</span>
            </div>
            <div className="text-3xl font-black text-amber-400">$48,500</div>
            <div className="text-xs mt-1 font-semibold text-amber-400/80">↑ 8% vs last month</div>
          </div>

          <div className="bg-gradient-to-br from-[#1e1e3f] to-[#161632] rounded-2xl p-5 border border-[#2d2d44] hover:border-[#3d3d5c] transition-all">
            <div className="flex justify-between items-center mb-2">
              <span className="text-xs font-bold text-[#64748b] uppercase tracking-wider">At-Risk Members</span>
              <span>⚠️</span>
            </div>
            <div className="text-3xl font-black text-red-400">14</div>
            <div className="text-xs mt-1 font-semibold text-red-400/80">↓ 5 reduced by AI</div>
          </div>

          <div className="bg-gradient-to-br from-[#1e1e3f] to-[#161632] rounded-2xl p-5 border border-[#2d2d44] hover:border-[#3d3d5c] transition-all">
            <div className="flex justify-between items-center mb-2">
              <span className="text-xs font-bold text-[#64748b] uppercase tracking-wider">Class Occupancy</span>
              <span>📊</span>
            </div>
            <div className="text-3xl font-black text-purple-400">87%</div>
            <div className="text-xs mt-1 font-semibold text-purple-400/80">Optimal capacity</div>
          </div>

          <div className="bg-gradient-to-br from-[#1e1e3f] to-[#161632] rounded-2xl p-5 border border-[#2d2d44] hover:border-[#3d3d5c] transition-all">
            <div className="flex justify-between items-center mb-2">
              <span className="text-xs font-bold text-[#64748b] uppercase tracking-wider">AI Actions Today</span>
              <span>🤖</span>
            </div>
            <div className="text-3xl font-black text-pink-400">147</div>
            <div className="text-xs mt-1 font-semibold text-pink-400/80">Automated outreach</div>
          </div>
        </div>

        {/* MIDDLE SECTION */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* AI ASSISTANT PANEL */}
          <div className="lg:col-span-7 bg-[#1e1e3f] border border-[#2d2d44] rounded-2xl p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-8 h-8 rounded-lg bg-indigo-500/20 text-indigo-400 flex items-center justify-center font-bold">🤖</div>
              <div>
                <h3 className="text-lg font-bold text-white">FitMind AI Copilot</h3>
                <p className="text-xs text-slate-400">Real-time gym recommendations & automated tasks</p>
              </div>
            </div>

            <div className="space-y-3">
              <div className="p-4 rounded-xl bg-[#161632] border border-[#2d2d44] flex items-start gap-3">
                <span className="text-amber-400 text-lg">💡</span>
                <div>
                  <h4 className="text-sm font-semibold text-white">Retention Alert: 4 Members missed 3+ workouts</h4>
                  <p className="text-xs text-slate-400 mt-1">AI sent personalized re-engagement SMS text messages automatically.</p>
                </div>
              </div>

              <div className="p-4 rounded-xl bg-[#161632] border border-[#2d2d44] flex items-start gap-3">
                <span className="text-emerald-400 text-lg">✨</span>
                <div>
                  <h4 className="text-sm font-semibold text-white">Class Optimization</h4>
                  <p className="text-xs text-slate-400 mt-1">Evening HIIT Class is at 100% capacity. AI suggests opening an extra 7:00 PM slot.</p>
                </div>
              </div>
            </div>
          </div>

          {/* CLASS SCHEDULE */}
          <div className="lg:col-span-5 bg-[#1e1e3f] border border-[#2d2d44] rounded-2xl p-6">
            <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
              📅 Today's Classes
            </h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center p-3 rounded-xl bg-[#161632] border border-[#2d2d44]">
                <div>
                  <div className="text-sm font-bold text-white">Power CrossFit</div>
                  <div className="text-xs text-slate-400">Coach Alex • 08:00 AM</div>
                </div>
                <span className="text-xs font-bold text-emerald-400 bg-emerald-950 px-2.5 py-1 rounded-full border border-emerald-800">Full (20/20)</span>
              </div>

              <div className="flex justify-between items-center p-3 rounded-xl bg-[#161632] border border-[#2d2d44]">
                <div>
                  <div className="text-sm font-bold text-white">Vinyasa Flow Yoga</div>
                  <div className="text-xs text-slate-400">Coach Elena • 10:30 AM</div>
                </div>
                <span className="text-xs font-bold text-indigo-400 bg-indigo-950 px-2.5 py-1 rounded-full border border-indigo-800">14/15 Slots</span>
              </div>

              <div className="flex justify-between items-center p-3 rounded-xl bg-[#161632] border border-[#2d2d44]">
                <div>
                  <div className="text-sm font-bold text-white">Hypertrophy Chest & Arms</div>
                  <div className="text-xs text-slate-400">Coach Marcus • 05:00 PM</div>
                </div>
                <span className="text-xs font-bold text-purple-400 bg-purple-950 px-2.5 py-1 rounded-full border border-purple-800">18/20 Slots</span>
              </div>
            </div>
          </div>
        </div>

        {/* RETENTION PIPELINE */}
        <div className="bg-[#1e1e3f] border border-[#2d2d44] rounded-2xl p-6">
          <h3 className="text-lg font-bold text-white mb-4">Member Retention & Churn Risk Pipeline</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-4 rounded-xl bg-[#161632] border border-[#2d2d44] text-center">
              <span className="text-xs text-slate-400 uppercase font-semibold">Low Risk</span>
              <div className="text-2xl font-bold text-emerald-400 mt-1">1,180</div>
            </div>
            <div className="p-4 rounded-xl bg-[#161632] border border-[#2d2d44] text-center">
              <span className="text-xs text-slate-400 uppercase font-semibold">Medium Risk</span>
              <div className="text-2xl font-bold text-amber-400 mt-1">54</div>
            </div>
            <div className="p-4 rounded-xl bg-[#161632] border border-[#2d2d44] text-center">
              <span className="text-xs text-slate-400 uppercase font-semibold">High Risk</span>
              <div className="text-2xl font-bold text-orange-400 mt-1">10</div>
            </div>
            <div className="p-4 rounded-xl bg-[#161632] border border-[#2d2d44] text-center">
              <span className="text-xs text-slate-400 uppercase font-semibold">Critical / Lost</span>
              <div className="text-2xl font-bold text-red-400 mt-1">4</div>
            </div>
          </div>
        </div>

      </main>
    </div>
  );
}
