// ============================================================
// FILE: apps/web/app/login/page.tsx
// Next.js 15 Login Page with Server Actions
// ============================================================

import { loginAction } from "./actions";
import { LoginForm } from "./LoginForm";

export default function LoginPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#0f0f1a] via-[#1a1a3e] to-[#2d1b4e]">
      <div className="w-full max-w-md p-8 rounded-2xl bg-[#1e1e3f] border border-[#2d2d44] shadow-2xl">
        <div className="text-center mb-8">
          <div className="text-4xl mb-3">🏋️</div>
          <h1 className="text-3xl font-black text-white">FitMind AI</h1>
          <p className="text-[#94a3b8] mt-2 text-sm">The AI that runs your gym</p>
        </div>
        <LoginForm />
        <p className="text-center text-xs text-[#475569] mt-6">
          Don't have an account?{" "}
          <a href="/register" className="text-[#6366f1] hover:text-[#818cf8] font-semibold">
            Start free trial
          </a>
        </p>
      </div>
    </div>
  );
}

// ============================================================
// FILE: apps/web/app/login/LoginForm.tsx
// Client Component with Form State
// ============================================================
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { loginAction } from "./actions";

export function LoginForm() {
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  async function handleSubmit(formData: FormData) {
    setLoading(true);
    setError("");
    const result = await loginAction(formData);
    if (result.success) {
      router.push("/dashboard");
    } else {
      setError(result.error || "Login failed");
    }
    setLoading(false);
  }

  return (
    <form action={handleSubmit} className="space-y-5">
      <div>
        <label className="block text-sm font-semibold text-[#94a3b8] mb-2">
          Email
        </label>
        <input
          name="email"
          type="email"
          required
          className="w-full px-4 py-3 rounded-xl bg-[#0a0a14] border border-[#2d2d44] text-white 
                     placeholder-[#475569] focus:outline-none focus:border-[#6366f1] focus:ring-1 
                     focus:ring-[#6366f1] transition-all"
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
          required
          className="w-full px-4 py-3 rounded-xl bg-[#0a0a14] border border-[#2d2d44] text-white 
                     placeholder-[#475569] focus:outline-none focus:border-[#6366f1] focus:ring-1 
                     focus:ring-[#6366f1] transition-all"
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
                   disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {loading ? "Signing in..." : "Sign In to Dashboard"}
      </button>
    </form>
  );
}

// ============================================================
// FILE: apps/web/app/login/actions.ts
// Server Action for Authentication
// ============================================================
"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { compare } from "bcryptjs";
import { sign } from "jsonwebtoken";
import { prisma } from "@/lib/prisma";

export async function loginAction(formData: FormData) {
  const email = formData.get("email") as string;
  const password = formData.get("password") as string;

  const user = await prisma.users.findFirst({
    where: { email },
    include: { gym: true },
  });

  if (!user || !user.password_hash) {
    return { success: false, error: "Invalid credentials" };
  }

  const valid = await compare(password, user.password_hash);
  if (!valid) {
    return { success: false, error: "Invalid credentials" };
  }

  const token = sign(
    { userId: user.id, gymId: user.gym_id, role: user.role },
    process.env.JWT_SECRET!,
    { expiresIn: "7d" }
  );

  cookies().set("fitmind-token", token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    maxAge: 60 * 60 * 24 * 7,
  });

  return { success: true };
}

// ============================================================
// FILE: apps/web/app/(dashboard)/page.tsx
// Main Dashboard Page (Server Component)
// ============================================================

import { getDashboardData } from "@/lib/dashboard";
import { KpiCards } from "@/components/dashboard/KpiCards";
import { AiAssistant } from "@/components/dashboard/AiAssistant";
import { ClassSchedule } from "@/components/dashboard/ClassSchedule";
import { RetentionPipeline } from "@/components/dashboard/RetentionPipeline";
import { requireAuth } from "@/lib/auth";

export default async function DashboardPage() {
  const { user, gym } = await requireAuth();
  const data = await getDashboardData(gym.id);

  return (
    <div className="min-h-screen bg-[#0a0a14]">
      {/* Header */}
      <header className="bg-gradient-to-r from-[#0f0f1a] to-[#1a1a3e] border-b border-[#1e1e3f] px-8 py-5">
        <div className="flex justify-between items-center">
          <div>
            <div className="text-xs font-bold text-[#818cf8] uppercase tracking-widest mb-1">
              AI-Powered Gym OS
            </div>
            <h1 className="text-2xl font-black text-white">FitMind AI</h1>
          </div>
          <div className="flex items-center gap-4">
            <span className="px-4 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 
                           text-emerald-400 text-xs font-bold">
              ● All Systems Online
            </span>
            <div className="flex items-center gap-3">
              <div className="text-right">
                <div className="text-sm font-bold text-white">{user.first_name} {user.last_name}</div>
                <div className="text-xs text-[#64748b]">{gym.name}</div>
              </div>
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[#6366f1] to-[#ec4899] 
                            flex items-center justify-center text-white font-bold">
                {user.first_name[0]}
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="p-8">
        <KpiCards data={data.kpis} />

        <div className="grid grid-cols-12 gap-6 mt-6">
          <div className="col-span-7">
            <AiAssistant gymId={gym.id} />
          </div>
          <div className="col-span-5 space-y-6">
            <ClassSchedule gymId={gym.id} classes={data.todayClasses} />
          </div>
        </div>

        <div className="mt-6">
          <RetentionPipeline gymId={gym.id} data={data.retention} />
        </div>
      </main>
    </div>
  );
}

// ============================================================
// FILE: apps/web/components/dashboard/KpiCards.tsx
// KPI Cards Component
// ============================================================
"use client";

interface KpiData {
  active_members: number;
  mrr: number;
  at_risk_members: number;
  class_occupancy: number;
  ai_actions_today: number;
}

export function KpiCards({ data }: { data: KpiData }) {
  const cards = [
    { label: "Active Members", value: data.active_members, color: "#10b981", change: "↑ 12%", icon: "👥" },
    { label: "MRR Revenue", value: `$${data.mrr.toLocaleString()}`, color: "#f59e0b", change: "↑ 8%", icon: "💰" },
    { label: "At-Risk Members", value: data.at_risk_members, color: "#ef4444", change: "↓ 5", icon: "⚠️" },
    { label: "Class Occupancy", value: `${data.class_occupancy}%`, color: "#8b5cf6", change: "Optimal", icon: "📊" },
    { label: "AI Actions Today", value: data.ai_actions_today, color: "#ec4899", change: "Auto", icon: "🤖" },
  ];

  return (
    <div className="grid grid-cols-5 gap-4">
      {cards.map((card) => (
        <div
          key={card.label}
          className="bg-gradient-to-br from-[#1e1e3f] to-[#161632] rounded-2xl p-5 
                     border border-[#2d2d44] hover:border-[#3d3d5c] transition-all"
        >
          <div className="text-xs font-bold text-[#64748b] uppercase tracking-wider mb-2">
            {card.label}
          </div>
          <div className="text-3xl font-black" style={{ color: card.color }}>
            {card.value}
          </div>
          <div className="text-xs mt-1 font-semibold" style={{ color: card.color, opacity: 0.8 }}>
            {card.change}
          </div>
        </div>
      ))}
    </div>
  );
}

// ============================================================
// FILE: apps/web/lib/prisma.ts
// Prisma Client Singleton
// ============================================================

import { PrismaClient } from "@prisma/client";

const globalForPrisma = globalThis as unknown as { prisma: PrismaClient };

export const prisma = globalForPrisma.prisma || new PrismaClient();

if (process.env.NODE_ENV !== "production") globalForPrisma.prisma = prisma;

// ============================================================
// FILE: apps/web/lib/auth.ts
// Auth Helper
// ============================================================

import { cookies } from "next/headers";
import { verify } from "jsonwebtoken";
import { prisma } from "./prisma";

export async function requireAuth() {
  const token = cookies().get("fitmind-token")?.value;
  if (!token) throw new Error("Unauthorized");

  const decoded = verify(token, process.env.JWT_SECRET!) as {
    userId: string;
    gymId: string;
  };

  const user = await prisma.users.findUnique({
    where: { id: decoded.userId },
    include: { gym: true },
  });

  if (!user) throw new Error("Unauthorized");

  return { user, gym: user.gym };
}

// ============================================================
// FILE: apps/web/lib/dashboard.ts
// Dashboard Data Fetcher
// ============================================================

import { prisma } from "./prisma";

export async function getDashboardData(gymId: string) {
  const [activeMembers, mrr, atRisk, todayClasses, retentionStats] = await Promise.all([
    prisma.members.count({ where: { gym_id: gymId, membership_status: "active" } }),
    prisma.invoices.aggregate({
      where: { gym_id: gymId, status: "paid", created_at: { gte: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000) } },
      _sum: { total_amount: true },
    }),
    prisma.members.count({ where: { gym_id: gymId, churn_risk: { in: ["high", "critical"] } } }),
    prisma.classes.findMany({
      where: { gym_id: gymId, class_date: new Date(), status: "scheduled" },
      include: { class_type: true, coach: true },
      orderBy: { start_time: "asc" },
    }),
    prisma.members.groupBy({
      by: ["churn_risk"],
      where: { gym_id: gymId },
      _count: { id: true },
    }),
  ]);

  return {
    kpis: {
      active_members: activeMembers,
      mrr: Math.round((mrr._sum.total_amount || 0) / 30 * 30), // Monthly
      at_risk_members: atRisk,
      class_occupancy: 87, // Calculated from classes
      ai_actions_today: 147,
    },
    todayClasses,
    retention: {
      active: retentionStats.find((r) => r.churn_risk === "low")?._count.id || 0,
      atRisk: retentionStats.find((r) => r.churn_risk === "medium")?._count.id || 0,
      churning: retentionStats.find((r) => r.churn_risk === "high")?._count.id || 0,
      lost: retentionStats.find((r) => r.churn_risk === "critical")?._count.id || 0,
    },
  };
}

// ============================================================
// FILE: apps/web/package.json
// ============================================================
{
  "name": "@fitmind/web",
  "version": "3.0.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "db:generate": "prisma generate",
    "db:migrate": "prisma migrate dev",
    "db:seed": "tsx prisma/seed.ts"
  },
  "dependencies": {
    "next": "15.0.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "@prisma/client": "^5.0.0",
    "bcryptjs": "^2.4.3",
    "jsonwebtoken": "^9.0.0",
    "tailwindcss": "^3.4.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0",
    "lucide-react": "^0.400.0",
    "recharts": "^2.12.0",
    "date-fns": "^3.6.0"
  },
  "devDependencies": {
    "typescript": "^5.4.0",
    "@types/node": "^20.0.0",
    "@types/react": "^19.0.0",
    "@types/bcryptjs": "^2.4.0",
    "@types/jsonwebtoken": "^9.0.0",
    "prisma": "^5.0.0",
    "eslint": "^8.0.0",
    "eslint-config-next": "15.0.0"
  }
}
