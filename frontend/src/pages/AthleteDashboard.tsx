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

  useEffect(() => { loadWorkouts(); }, []);

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

  const handleRemove = async (id: number) => {
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
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="font-display text-2xl font-bold text-gray-900 mb-2">My Workouts</h1>
      <p className="text-gray-600 mb-6">
        {user?.garmin_connected
          ? "Your Garmin account is connected. You can import workouts below."
          : "Connect your Garmin account in Settings to import workouts to your watch."}
      </p>

      {/* Pending Workouts */}
      <div className="card mb-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold">
            Ready to Import ({pendingWorkouts.length})
          </h2>
          {pendingWorkouts.length > 0 && (
            <button
              onClick={handleImport}
              disabled={importing || selectedIds.size === 0 || !user?.garmin_connected}
              className="btn-primary text-sm py-2"
            >
              {importing
                ? "Importing..."
                : `Import ${selectedIds.size} selected`}
            </button>
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
                  onClick={() => handleRemove(w.id)}
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
