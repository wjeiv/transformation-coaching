import React, { useEffect, useState } from "react";
import { coachAPI } from "../services/api";
import toast from "react-hot-toast";

interface Athlete {
  id: number;
  full_name: string;
  email: string;
  garmin_connected: boolean;
  last_login: string | null;
}

interface User {
  id: number;
  full_name: string;
  email: string;
  role: string;
  is_active: boolean;
  avatar_url: string | null;
  coach_id: number | null;
  created_at: string;
  last_login: string | null;
  garmin_connected: boolean;
}

interface GarminWorkout {
  garmin_workout_id: string;
  workout_name: string;
  workout_type: string;
  description: string | null;
}

interface ConnectionCheck {
  athlete_id: number;
  is_connected: boolean;
  athlete_name: string;
  garmin_email: string | null;
  error_message: string | null;
  recommendations: string[];
}

const workoutTypeColors: Record<string, string> = {
  running: "bg-orange-100 text-orange-700",
  cycling: "bg-blue-100 text-blue-700",
  swimming: "bg-cyan-100 text-cyan-700",
  strength: "bg-purple-100 text-purple-700",
  other: "bg-gray-100 text-gray-700",
};

const CoachDashboard: React.FC = () => {
  const [athletes, setAthletes] = useState<Athlete[]>([]);
  const [workouts, setWorkouts] = useState<GarminWorkout[]>([]);
  const [selectedWorkouts, setSelectedWorkouts] = useState<Set<string>>(new Set());
  const [selectedAthlete, setSelectedAthlete] = useState<number | null>(null);
  const [connectionCheck, setConnectionCheck] = useState<ConnectionCheck | null>(null);
  const [typeFilter, setTypeFilter] = useState("");
  const [loadingWorkouts, setLoadingWorkouts] = useState(false);
  const [sharing, setSharing] = useState(false);
  const [checkingConnection, setCheckingConnection] = useState(false);

  // Link athletes state
  const [allUsers, setAllUsers] = useState<User[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [roleFilter, setRoleFilter] = useState("all");
  const [onlyUnlinked, setOnlyUnlinked] = useState(false);
  const [loadingUsers, setLoadingUsers] = useState(false);
  const [linkingUserId, setLinkingUserId] = useState<number | null>(null);

  useEffect(() => {
    coachAPI.listAthletes().then((r) => setAthletes(r.data)).catch(() => {});
  }, []);

  const loadUsers = async () => {
    setLoadingUsers(true);
    try {
      const params: any = {};
      if (searchTerm) params.search = searchTerm;
      if (roleFilter !== "all") params.role = roleFilter;
      if (onlyUnlinked) params.only_unlinked = true;
      const resp = await coachAPI.listUsers(params);
      setAllUsers(resp.data.users);
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Failed to load users");
    } finally {
      setLoadingUsers(false);
    }
  };

  useEffect(() => {
    loadUsers();
  }, [searchTerm, roleFilter, onlyUnlinked]);

  const loadWorkouts = async () => {
    setLoadingWorkouts(true);
    try {
      const resp = await coachAPI.getWorkouts(typeFilter || undefined);
      setWorkouts(resp.data.workouts);
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Failed to load workouts from Garmin");
    } finally {
      setLoadingWorkouts(false);
    }
  };

  useEffect(() => { loadWorkouts(); }, [typeFilter]);

  const toggleWorkout = (id: string) => {
    const next = new Set(selectedWorkouts);
    if (next.has(id)) next.delete(id); else next.add(id);
    setSelectedWorkouts(next);
  };

  const handleCheckConnection = async (athleteId: number) => {
    setCheckingConnection(true);
    setConnectionCheck(null);
    try {
      const resp = await coachAPI.checkAthleteConnection(athleteId);
      setConnectionCheck(resp.data);
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Failed to check connection");
    } finally {
      setCheckingConnection(false);
    }
  };

  const handleSelectAthlete = (athleteId: number) => {
    setSelectedAthlete(athleteId);
    setConnectionCheck(null);
    handleCheckConnection(athleteId);
  };

  const handleShare = async () => {
    if (!selectedAthlete || selectedWorkouts.size === 0) {
      toast.error("Select at least one workout and an athlete");
      return;
    }
    setSharing(true);
    try {
      const resp = await coachAPI.shareWorkouts(Array.from(selectedWorkouts), selectedAthlete);
      toast.success(resp.data.message);
      if (resp.data.errors?.length > 0) {
        resp.data.errors.forEach((e: string) => toast.error(e, { duration: 5000 }));
      }
      setSelectedWorkouts(new Set());
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Failed to share workouts");
    } finally {
      setSharing(false);
    }
  };

  const handleLinkUser = async (userId: number) => {
    setLinkingUserId(userId);
    try {
      await coachAPI.linkAthlete(userId);
      toast.success("Athlete linked successfully!");
      // Refresh both lists
      loadUsers();
      coachAPI.listAthletes().then((r) => setAthletes(r.data)).catch(() => {});
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Failed to link athlete");
    } finally {
      setLinkingUserId(null);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="font-display text-2xl font-bold text-gray-900 mb-6">Coach Dashboard</h1>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Athletes Panel */}
        <div className="card lg:col-span-1">
          <h2 className="text-lg font-semibold mb-4">My Athletes</h2>
          {athletes.length === 0 ? (
            <p className="text-sm text-gray-500">No athletes linked yet. Athletes can select you as their coach from their account.</p>
          ) : (
            <div className="space-y-2">
              {athletes.map((a) => (
                <button
                  key={a.id}
                  onClick={() => handleSelectAthlete(a.id)}
                  className={`w-full text-left p-3 rounded-lg border transition-all ${
                    selectedAthlete === a.id
                      ? "border-dragonfly bg-dragonfly/5"
                      : "border-gray-200 hover:border-gray-300"
                  }`}
                >
                  <div className="font-medium text-sm">{a.full_name}</div>
                  <div className="text-xs text-gray-500">{a.email}</div>
                  <div className="flex gap-2 mt-1">
                    <span className={`text-xs ${a.garmin_connected ? "text-green-600" : "text-gray-400"}`}>
                      {a.garmin_connected ? "Garmin ✓" : "No Garmin"}
                    </span>
                  </div>
                </button>
              ))}
            </div>
          )}

          {/* Connection Check */}
          {connectionCheck && (
            <div className={`mt-4 p-3 rounded-lg text-sm ${
              connectionCheck.is_connected ? "bg-green-50 border border-green-200" : "bg-red-50 border border-red-200"
            }`}>
              <div className={`font-medium ${connectionCheck.is_connected ? "text-green-700" : "text-red-700"}`}>
                {connectionCheck.is_connected ? "✓ Ready for sync" : "✗ Connection issue"}
              </div>
              {connectionCheck.error_message && (
                <p className="text-red-600 mt-1">{connectionCheck.error_message}</p>
              )}
              {connectionCheck.recommendations.length > 0 && (
                <ul className="mt-2 space-y-1">
                  {connectionCheck.recommendations.map((r, i) => (
                    <li key={i} className="text-gray-600">• {r}</li>
                  ))}
                </ul>
              )}
            </div>
          )}
          {checkingConnection && (
            <div className="mt-4 text-sm text-gray-500 animate-pulse">Checking Garmin connection...</div>
          )}
        </div>

        {/* Link Athletes Panel */}
        <div className="card lg:col-span-2">
          <h2 className="text-lg font-semibold mb-4">Link Athletes</h2>
          
          {/* Search and Filters */}
          <div className="flex flex-col sm:flex-row gap-3 mb-4">
            <input
              type="text"
              placeholder="Search by name or email..."
              className="input-field text-sm"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
            <select
              className="input-field text-sm"
              value={roleFilter}
              onChange={(e) => setRoleFilter(e.target.value)}
            >
              <option value="all">All Roles</option>
              <option value="athlete">Athletes Only</option>
              <option value="coach">Coaches Only</option>
            </select>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={onlyUnlinked}
                onChange={(e) => setOnlyUnlinked(e.target.checked)}
                className="rounded border-gray-300 text-dragonfly focus:ring-dragonfly"
              />
              Only unlinked athletes
            </label>
          </div>

          {/* Users List */}
          {loadingUsers ? (
            <div className="text-center py-8 text-gray-500 animate-pulse">Loading users...</div>
          ) : allUsers.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <p className="text-sm">No users found matching your criteria.</p>
            </div>
          ) : (
            <div className="space-y-2 max-h-[400px] overflow-y-auto">
              {allUsers.map((user) => (
                <div
                  key={user.id}
                  className="flex items-center justify-between p-3 rounded-lg border border-gray-200 hover:border-gray-300 transition-all"
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <div className="font-medium text-sm truncate">{user.full_name}</div>
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                        user.role === "athlete" ? "bg-blue-100 text-blue-700" : "bg-purple-100 text-purple-700"
                      }`}>
                        {user.role}
                      </span>
                      {user.coach_id && (
                        <span className="text-xs text-gray-500">Already linked</span>
                      )}
                    </div>
                    <div className="text-xs text-gray-500 truncate">{user.email}</div>
                  </div>
                  {user.role === "athlete" && !user.coach_id ? (
                    <button
                      onClick={() => handleLinkUser(user.id)}
                      disabled={linkingUserId === user.id}
                      className="btn-primary text-sm py-1 px-3"
                    >
                      {linkingUserId === user.id ? "Linking..." : "Link"}
                    </button>
                  ) : (
                    <button
                      disabled
                      className="btn-secondary text-sm py-1 px-3 opacity-50 cursor-not-allowed"
                    >
                      {user.role !== "athlete" ? "Not an athlete" : "Already linked"}
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Workouts Panel */}
      <div className="card mt-6">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 mb-4">
          <h2 className="text-lg font-semibold">Garmin Workouts</h2>
          <div className="flex gap-2">
            <select
              className="input-field text-sm py-2 w-36"
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
            >
              <option value="">All Types</option>
              <option value="running">Running</option>
              <option value="cycling">Cycling</option>
              <option value="swimming">Swimming</option>
              <option value="strength">Strength</option>
            </select>
            <button onClick={loadWorkouts} disabled={loadingWorkouts} className="btn-secondary text-sm py-2">
              {loadingWorkouts ? "Loading..." : "Refresh"}
            </button>
          </div>
        </div>

        {workouts.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <p className="text-sm">No workouts found. Connect your Garmin account in Settings to see your workouts here.</p>
          </div>
        ) : (
          <div className="space-y-2 max-h-[500px] overflow-y-auto">
            {workouts.map((w) => (
              <label
                key={w.garmin_workout_id}
                className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-all ${
                  selectedWorkouts.has(w.garmin_workout_id)
                    ? "border-dragonfly bg-dragonfly/5"
                    : "border-gray-200 hover:border-gray-300"
                }`}
              >
                <input
                  type="checkbox"
                  checked={selectedWorkouts.has(w.garmin_workout_id)}
                  onChange={() => toggleWorkout(w.garmin_workout_id)}
                  className="rounded border-gray-300 text-dragonfly focus:ring-dragonfly"
                />
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-sm truncate">{w.workout_name}</div>
                  {w.description && (
                    <div className="text-xs text-gray-500 truncate">{w.description}</div>
                  )}
                </div>
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                  workoutTypeColors[w.workout_type] || workoutTypeColors.other
                }`}>
                  {w.workout_type}
                </span>
              </label>
            ))}
          </div>
        )}

        {/* Share Button */}
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="relative group inline-block w-full sm:w-auto">
            <button
              onClick={handleShare}
              disabled={sharing || selectedWorkouts.size === 0 || !selectedAthlete || (connectionCheck !== null && !connectionCheck.is_connected)}
              className="btn-primary w-full sm:w-auto"
            >
              {sharing
                ? "Sharing..."
                : `Share ${selectedWorkouts.size} workout${selectedWorkouts.size !== 1 ? "s" : ""} with athlete`}
            </button>
            {!selectedAthlete && selectedWorkouts.size > 0 && (
              <p className="text-sm text-amber-600 mt-2">
                Select an athlete from "My Athletes" above to share workouts with them.
              </p>
            )}
            {selectedAthlete && selectedWorkouts.size === 0 && (
              <p className="text-sm text-amber-600 mt-2">
                Select one or more workouts from the list above to share.
              </p>
            )}
            {!selectedAthlete && selectedWorkouts.size === 0 && (
              <p className="text-sm text-gray-500 mt-2">
                Select an athlete and one or more workouts to enable sharing.
              </p>
            )}
          </div>
          {selectedAthlete && connectionCheck && !connectionCheck.is_connected && (
            <p className="text-sm text-red-600 mt-2">
              Cannot share — athlete's Garmin connection has issues. See recommendations above.
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

export default CoachDashboard;
