
import React, { useState } from "react";
import Head from "next/head";

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

  return (
    <>
      <Head>
        <title>FitMind AI - Gym OS</title>
        {/* Forces Tailwind CSS styling to load directly */}
        <script src="https://cdn.tailwindcss.com"></script>
      </Head>

      {/* ============================================================ */}
      {/* 1. LOGIN SCREEN VIEW                                         */}
      {/* ============================================================ */}
      {!isLoggedIn ? (
                           disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-indigo-500/20 cursor-pointer"
              >
                {loading ? "Signing in..." : "Sign In to Dashboard"}
              </button>
            </form>

            <p className="text-center text-xs text-[#475569] mt-6">
              Don't have an account?{" "}
              <a
                href="#"
                onClick={(e) => { e.preventDefault(); setIsLoggedIn(true); }}
                className="text-[#6366f1] hover:text-[#818cf8] font-semibold"
              >
                Start free trial
              </a>
            </p>
          </div>
        </div>
      ) : (
        /* ============================================================ */
        /* 2. MAIN GYM OS DASHBOARD VIEW                                */
        /* ============================================================ */
        <div className="min-h-screen bg-[#0a0a14] font-sans text-slate-100">
                    className="text-xs text-slate-400 hover:text-white bg-[#1e1e3f] border border-[#2d2d44] px-3 py-1.5 rounded-lg transition cursor-pointer"
                  >
                    Sign Out
                  </button>
                </div>
              </div>
            </div>
          </header>

          <main className="p-6 md:p-8 max-w-7xl mx-auto space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
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
      )}
    </>
  );
}
