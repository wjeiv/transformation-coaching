import React, { useEffect, useState } from "react";
import { athleteAPI } from "../services/api";
import { useAuth } from "../context/AuthContext";
import toast from "react-hot-toast";

interface SharedWorkout {
  id: number;
  workout_name: string;
  workout_type: string;
  description: string | null;
  coach_name: string;
  status: string;
  shared_at: string;
  imported_at: string | null;
  import_error: string | null;
}

interface Coach {
  id: number;
  full_name: string;
  email: string;
}

const workoutTypeColors: Record<string, string> = {
  running: "bg-orange-100 text-orange-700",
  cycling: "bg-blue-100 text-blue-700",
  swimming: "bg-cyan-100 text-cyan-700",
  strength: "bg-purple-100 text-purple-700",
  other: "bg-gray-100 text-gray-700",
};

const statusColors: Record<string, string> = {
  pending: "bg-yellow-100 text-yellow-700",
  imported: "bg-green-100 text-green-700",
  failed: "bg-red-100 text-red-700",
};

const AthleteDashboard: React.FC = () => {
  const { user } = useAuth();
  const [workouts, setWorkouts] = useState<SharedWorkout[]>([]);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [importing, setImporting] = useState(false);
  const [loading, setLoading] = useState(true);
  const [coach, setCoach] = useState<Coach | null>(null);
  const [inspirationalQuote, setInspirationalQuote] = useState<string>("");

  const generateInspirationalQuote = () => {
    const quotes = [
      "Every workout is a step closer to your goals. Keep pushing forward! 💪",
      "Your only limit is you. Push beyond your comfort zone today! 🎯",
      "Success is the sum of small efforts repeated day in and day out. 🌟",
      "The pain you feel today will be the strength you feel tomorrow. 🔥",
      "Champions are made when no one is watching. Keep grinding! 🏆",
      "Your body can stand almost anything. It's your mind you have to convince. 💭",
      "The hard days are what make you stronger. Embrace the challenge! ⚡",
      "Progress, not perfection. Every rep counts! 📈",
      "You're stronger than you think. Believe in yourself! ✨",
      "The journey of a thousand miles begins with a single step. Start today! 🚀"
    ];
    return quotes[Math.floor(Math.random() * quotes.length)];
  };

  const loadCoachInfo = async () => {
    try {
      const resp = await athleteAPI.listCoaches();
      if (resp.data.length > 0) {
        setCoach(resp.data[0]);
      }
    } catch {
      // Silently fail if coach info is not available
    }
  };

  const loadWorkouts = async () => {
    setLoading(true);
    try {
      const resp = await athleteAPI.getWorkouts();
      setWorkouts(resp.data.workouts);
    } catch {
      toast.error("Failed to load workouts");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { 
    loadWorkouts(); 
    loadCoachInfo();
    setInspirationalQuote(generateInspirationalQuote());
  }, []);

  const toggleSelect = (id: number) => {
    const next = new Set(selectedIds);
    if (next.has(id)) next.delete(id); else next.add(id);
    setSelectedIds(next);
  };

  const handleImport = async () => {
    if (selectedIds.size === 0) return;
    setImporting(true);
    try {
      const resp = await athleteAPI.importWorkouts(Array.from(selectedIds));
      const results = resp.data;
      let successCount = 0;
      results.forEach((r: any) => {
        if (r.success) {
          successCount++;
          toast.success(r.message, { duration: 4000 });
        } else {
          toast.error(r.message, { duration: 6000 });
        }
      });
      if (successCount > 0) {
        setSelectedIds(new Set());
        loadWorkouts();
      }
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Import failed");
    } finally {
      setImporting(false);
    }
  };

  const handleRemove = async (id: number, workoutStatus: string) => {
    if (workoutStatus === "pending") {
      if (!window.confirm("This workout has not been imported yet. Are you sure you want to remove it?")) {
        return;
      }
    }
    try {
      await athleteAPI.removeWorkout(id);
      toast.success("Workout removed");
      loadWorkouts();
    } catch {
      toast.error("Failed to remove workout");
    }
  };

  const pendingWorkouts = workouts.filter((w) => w.status === "pending" || w.status === "failed");
  const importedWorkouts = workouts.filter((w) => w.status === "imported");

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="font-display text-2xl font-bold text-gray-900 mb-6">Athlete Dashboard</h1>

      {/* Dashboard Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {/* Coach Info Card */}
        <div className="card">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-dragonfly/10 rounded-full flex items-center justify-center">
              <span className="text-dragonfly font-semibold">👨‍🏫</span>
            </div>
            <h3 className="font-semibold text-gray-900">Your Coach</h3>
          </div>
          {coach ? (
            <div>
              <p className="font-medium text-gray-900">{coach.full_name}</p>
              <p className="text-sm text-gray-500">{coach.email}</p>
            </div>
          ) : (
            <p className="text-sm text-gray-500">No coach assigned</p>
          )}
        </div>

        {/* Workouts Shared Card */}
        <div className="card">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
              <span className="text-blue-600 font-semibold">📋</span>
            </div>
            <h3 className="font-semibold text-gray-900">Workouts Shared</h3>
          </div>
          <p className="text-2xl font-bold text-gray-900">{workouts.length}</p>
          <p className="text-sm text-gray-500">Total from coach</p>
        </div>

        {/* Workouts Imported Card */}
        <div className="card">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
              <span className="text-green-600 font-semibold">✅</span>
            </div>
            <h3 className="font-semibold text-gray-900">Imported</h3>
          </div>
          <p className="text-2xl font-bold text-gray-900">{importedWorkouts.length}</p>
          <p className="text-sm text-gray-500">Successfully imported</p>
        </div>

        {/* Garmin Status Card */}
        <div className="card">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-orange-100 rounded-full flex items-center justify-center">
              <span className="text-orange-600 font-semibold">⌚</span>
            </div>
            <h3 className="font-semibold text-gray-900">Garmin Status</h3>
          </div>
          <p className={`font-medium ${user?.garmin_connected ? "text-green-600" : "text-gray-500"}`}>
            {user?.garmin_connected ? "Connected" : "Not Connected"}
          </p>
          <p className="text-sm text-gray-500">
            {user?.garmin_connected ? "Ready to import" : "Connect in Settings"}
          </p>
        </div>
      </div>

      {/* Inspirational Quote */}
      <div className="card bg-gradient-to-r from-dragonfly/5 to-blue-50 border-l-4 border-dragonfly mb-8">
        <div className="flex items-start gap-3">
          <span className="text-2xl">💫</span>
          <div>
            <h3 className="font-semibold text-gray-900 mb-1">Daily Inspiration</h3>
            <p className="text-gray-700 italic">"{inspirationalQuote}"</p>
            <button 
              onClick={() => setInspirationalQuote(generateInspirationalQuote())}
              className="text-xs text-dragonfly hover:text-dragonfly-dark mt-2 transition-colors"
            >
              🔄 New Quote
            </button>
          </div>
        </div>
      </div>

      {/* Pending Workouts */}
      <div className="card mb-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold">
            Ready to Import ({pendingWorkouts.length})
          </h2>
          {pendingWorkouts.length > 0 && (
            <div className="text-right">
              <button
                onClick={handleImport}
                disabled={importing || selectedIds.size === 0 || !user?.garmin_connected}
                className="btn-primary text-sm py-2"
              >
                {importing
                  ? "Importing..."
                  : `Import ${selectedIds.size} selected`}
              </button>
              {!user?.garmin_connected && selectedIds.size > 0 && (
                <p className="text-xs text-amber-600 mt-1">
                  Connect your Garmin account in Settings to import workouts.
                </p>
              )}
              {user?.garmin_connected && selectedIds.size === 0 && (
                <p className="text-xs text-amber-600 mt-1">
                  Select workouts above to import them to your Garmin.
                </p>
              )}
            </div>
          )}
        </div>

        {loading ? (
          <div className="text-center py-8 text-gray-500 animate-pulse">Loading workouts...</div>
        ) : pendingWorkouts.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <p className="text-sm">No workouts waiting. Your coach will share workouts with you here.</p>
          </div>
        ) : (
          <div className="space-y-2">
            {pendingWorkouts.map((w) => (
              <label
                key={w.id}
                className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-all ${
                  selectedIds.has(w.id)
                    ? "border-dragonfly bg-dragonfly/5"
                    : "border-gray-200 hover:border-gray-300"
                }`}
              >
                <input
                  type="checkbox"
                  checked={selectedIds.has(w.id)}
                  onChange={() => toggleSelect(w.id)}
                  className="rounded border-gray-300 text-dragonfly focus:ring-dragonfly"
                />
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-sm">{w.workout_name}</div>
                  <div className="text-xs text-gray-500">
                    From {w.coach_name} &middot; {new Date(w.shared_at).toLocaleDateString()}
                  </div>
                  {w.description && (
                    <div className="text-xs text-gray-400 mt-0.5 truncate">{w.description}</div>
                  )}
                  {w.import_error && (
                    <div className="text-xs text-red-600 mt-1">Last error: {w.import_error}</div>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                    workoutTypeColors[w.workout_type] || workoutTypeColors.other
                  }`}>
                    {w.workout_type}
                  </span>
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                    statusColors[w.status] || "bg-gray-100 text-gray-700"
                  }`}>
                    {w.status}
                  </span>
                  <button
                    onClick={(e) => { e.preventDefault(); handleRemove(w.id, w.status); }}
                    className="text-xs text-gray-400 hover:text-red-600 transition-colors ml-1"
                  >
                    Remove
                  </button>
                </div>
              </label>
            ))}
          </div>
        )}
      </div>

      {/* Imported Workouts */}
      {importedWorkouts.length > 0 && (
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">
            Previously Imported ({importedWorkouts.length})
          </h2>
          <div className="space-y-2">
            {importedWorkouts.map((w) => (
              <div
                key={w.id}
                className="flex items-center gap-3 p-3 rounded-lg border border-gray-200"
              >
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-sm">{w.workout_name}</div>
                  <div className="text-xs text-gray-500">
                    Imported {w.imported_at ? new Date(w.imported_at).toLocaleDateString() : ""}
                  </div>
                </div>
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                  workoutTypeColors[w.workout_type] || workoutTypeColors.other
                }`}>
                  {w.workout_type}
                </span>
                <button
                  onClick={() => handleRemove(w.id, w.status)}
                  className="text-xs text-gray-400 hover:text-red-600 transition-colors"
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default AthleteDashboard;
