
import React from "react";

export default function Home() {
  return (
    <div className="min-h-screen bg-slate-900 text-white flex flex-col items-center justify-center p-6 text-center">
      <div className="max-w-md w-full bg-slate-800 p-8 rounded-2xl shadow-xl border border-slate-700">
        <h1 className="text-3xl font-extrabold text-blue-400 mb-2">FitMind AI</h1>
        <p className="text-slate-400 mb-6 text-sm">
          Your AI-Powered Health & Gym Companion
        </p>

        <div className="bg-slate-900/60 p-4 rounded-lg border border-slate-700 mb-6">
          <p className="text-emerald-400 font-semibold text-sm">
            ✓ System Operational
          </p>
          <p className="text-xs text-slate-500 mt-1">
            Frontend successfully deployed on Vercel
          </p>
        </div>

        <button className="w-full bg-blue-600 hover:bg-blue-500 text-white font-medium py-2.5 px-4 rounded-lg transition duration-200">
          Get Started
        </button>
      </div>
    </div>
  );
}
