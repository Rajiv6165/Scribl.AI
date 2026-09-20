"use client";

import React, { useEffect, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell
} from "recharts";
import { ShieldAlert, Users, Brain, Gamepad2, TrendingUp, AlertCircle, Clock } from "lucide-react";

// TODO: In a real production application, this page should be protected by
// host or admin authentication so that general players cannot see global analytics.
// Kept public for portfolio demonstration purposes.

type AnalyticsData = {
  most_drawn_words: { word: string; count: number }[];
  avg_guess_times: { difficulty: string; avg_seconds: number }[];
  accuracy: { is_ai: boolean; total_guesses: number; correct_guesses: number; accuracy_rate: number }[];
  flags_timeline: { date: string; flags: number }[];
  mode_popularity: { mode: string; rounds_played: number }[];
};

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'];

export default function StatsPage() {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/analytics/summary/`
        );
        if (!res.ok) {
          throw new Error("Failed to load analytics");
        }
        const json = await res.json();
        setData(json);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  if (loading) {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-zinc-950 text-zinc-300">
        <div className="animate-pulse flex flex-col items-center">
          <TrendingUp className="h-12 w-12 text-blue-500 mb-4" />
          <p className="text-xl font-semibold">Loading Analytics...</p>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-zinc-950 text-zinc-300">
        <div className="flex flex-col items-center p-8 bg-zinc-900 rounded-2xl border border-red-900/50">
          <AlertCircle className="h-12 w-12 text-red-500 mb-4" />
          <p className="text-xl font-semibold text-red-400">Error Loading Stats</p>
          <p className="text-zinc-500 mt-2">{error}</p>
        </div>
      </div>
    );
  }

  // Derived metrics
  const totalFlags = data.flags_timeline.reduce((acc, curr) => acc + curr.flags, 0);
  const aiAcc = data.accuracy.find((a) => a.is_ai)?.accuracy_rate || 0;
  const humanAcc = data.accuracy.find((a) => !a.is_ai)?.accuracy_rate || 0;

  // Format accuracy for charting
  const accuracyChartData = [
    { name: "Scribl-Bot", accuracy: Math.round(aiAcc * 100) },
    { name: "Human", accuracy: Math.round(humanAcc * 100) },
  ];

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-200 p-6 font-sans">
      <div className="max-w-7xl mx-auto space-y-8">
        
        {/* Header */}
        <div className="flex flex-col gap-2 border-b border-zinc-800 pb-6">
          <h1 className="text-4xl font-bold tracking-tight text-white flex items-center gap-3">
            <TrendingUp className="text-blue-500 h-8 w-8" /> 
            Global Analytics
          </h1>
          <p className="text-zinc-400">
            Real-time insights across all Scribl.AI games.
          </p>
        </div>

        {/* Top KPIs */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-zinc-900/50 border border-zinc-800 p-6 rounded-2xl flex items-center gap-4 hover:border-blue-500/50 transition-colors">
            <div className="p-4 bg-blue-500/10 rounded-xl text-blue-400">
              <Brain className="h-8 w-8" />
            </div>
            <div>
              <p className="text-zinc-500 text-sm font-medium uppercase tracking-wider">AI Accuracy</p>
              <p className="text-3xl font-bold text-white">{Math.round(aiAcc * 100)}%</p>
            </div>
          </div>
          <div className="bg-zinc-900/50 border border-zinc-800 p-6 rounded-2xl flex items-center gap-4 hover:border-green-500/50 transition-colors">
            <div className="p-4 bg-green-500/10 rounded-xl text-green-400">
              <Users className="h-8 w-8" />
            </div>
            <div>
              <p className="text-zinc-500 text-sm font-medium uppercase tracking-wider">Human Accuracy</p>
              <p className="text-3xl font-bold text-white">{Math.round(humanAcc * 100)}%</p>
            </div>
          </div>
          <div className="bg-zinc-900/50 border border-red-900/30 p-6 rounded-2xl flex items-center gap-4 hover:border-red-500/50 transition-colors">
            <div className="p-4 bg-red-500/10 rounded-xl text-red-400">
              <ShieldAlert className="h-8 w-8" />
            </div>
            <div>
              <p className="text-zinc-500 text-sm font-medium uppercase tracking-wider">Total Anti-Cheat Flags</p>
              <p className="text-3xl font-bold text-white">{totalFlags}</p>
            </div>
          </div>
        </div>

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          
          {/* Most Drawn Words */}
          <div className="bg-zinc-900/40 border border-zinc-800 rounded-3xl p-6">
            <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
              <Gamepad2 className="h-5 w-5 text-indigo-400" />
              Most Frequently Drawn Words
            </h2>
            <div className="h-80 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data.most_drawn_words} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#3f3f46" horizontal={false} />
                  <XAxis type="number" stroke="#a1a1aa" />
                  <YAxis dataKey="word" type="category" stroke="#a1a1aa" width={80} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#18181b', borderColor: '#27272a', color: '#f4f4f5' }}
                    itemStyle={{ color: '#818cf8' }}
                  />
                  <Bar dataKey="count" fill="#818cf8" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Game Mode Popularity */}
          <div className="bg-zinc-900/40 border border-zinc-800 rounded-3xl p-6">
            <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
              <Gamepad2 className="h-5 w-5 text-fuchsia-400" />
              Game Mode Popularity
            </h2>
            <div className="h-80 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={data.mode_popularity}
                    dataKey="rounds_played"
                    nameKey="mode"
                    cx="50%"
                    cy="50%"
                    outerRadius={100}
                    innerRadius={60}
                    label={({ mode, rounds_played }) => `${mode} (${rounds_played})`}
                  >
                    {data.mode_popularity.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#18181b', borderColor: '#27272a', color: '#f4f4f5' }} 
                  />
                  <Legend verticalAlign="bottom" height={36} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Anti-Cheat Flags Timeline */}
          <div className="bg-zinc-900/40 border border-zinc-800 rounded-3xl p-6">
            <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
              <ShieldAlert className="h-5 w-5 text-red-400" />
              Anti-Cheat Flags Over Time
            </h2>
            <div className="h-80 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data.flags_timeline}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#3f3f46" />
                  <XAxis dataKey="date" stroke="#a1a1aa" />
                  <YAxis stroke="#a1a1aa" allowDecimals={false} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#18181b', borderColor: '#27272a', color: '#f4f4f5' }}
                  />
                  <Line type="monotone" dataKey="flags" stroke="#ef4444" strokeWidth={3} dot={{ r: 5 }} activeDot={{ r: 8 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Guess Times */}
          <div className="bg-zinc-900/40 border border-zinc-800 rounded-3xl p-6">
            <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
              <Clock className="h-5 w-5 text-amber-400" />
              Avg Guess Time by Difficulty (s)
            </h2>
            <div className="h-80 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data.avg_guess_times} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#3f3f46" vertical={false} />
                  <XAxis dataKey="difficulty" stroke="#a1a1aa" />
                  <YAxis stroke="#a1a1aa" />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#18181b', borderColor: '#27272a', color: '#f4f4f5' }}
                    itemStyle={{ color: '#fbbf24' }}
                    cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                  />
                  <Bar dataKey="avg_seconds" fill="#fbbf24" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
