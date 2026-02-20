import React, { useEffect, useState } from "react";
import { authAPI, garminAPI } from "../services/api";
import { useAuth } from "../context/AuthContext";
import toast from "react-hot-toast";

interface GarminStatus {
  is_connected: boolean;
  last_sync: string | null;
  error_message: string | null;
  garmin_email: string | null;
}

const SettingsPage: React.FC = () => {
  const { user, refreshUser } = useAuth();
  const [garminStatus, setGarminStatus] = useState<GarminStatus | null>(null);
  const [garminEmail, setGarminEmail] = useState("");
  const [garminPassword, setGarminPassword] = useState("");
  const [connecting, setConnecting] = useState(false);
  const [testing, setTesting] = useState(false);

  // Profile editing state
  const [editingProfile, setEditingProfile] = useState(false);
  const [profileName, setProfileName] = useState("");
  const [profileAvatar, setProfileAvatar] = useState("");
  const [profileVenmo, setProfileVenmo] = useState("");
  const [savingProfile, setSavingProfile] = useState(false);

  useEffect(() => {
    if (user) {
      setProfileName(user.full_name || "");
      setProfileAvatar(user.avatar_url || "");
      setProfileVenmo(user.venmo_link || "");
    }
  }, [user]);

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingProfile(true);
    try {
      await authAPI.updateMe({
        full_name: profileName,
        avatar_url: profileAvatar || undefined,
        venmo_link: profileVenmo || undefined,
      });
      toast.success("Profile updated");
      setEditingProfile(false);
      refreshUser();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Failed to update profile");
    } finally {
      setSavingProfile(false);
    }
  };

  const loadGarminStatus = async () => {
    try {
      const resp = await garminAPI.getStatus();
      setGarminStatus(resp.data);
    } catch {
      // Not connected
    }
  };

  useEffect(() => { loadGarminStatus(); }, []);

  const handleConnect = async (e: React.FormEvent) => {
    e.preventDefault();
    setConnecting(true);
    try {
      const resp = await garminAPI.connect(garminEmail, garminPassword);
      toast.success(resp.data.message);
      setGarminPassword("");
      loadGarminStatus();
      refreshUser();
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      if (typeof detail === "object" && detail.message) {
        toast.error(detail.message, { duration: 6000 });
        if (detail.help) {
          detail.help.forEach((h: string) => toast(h, { icon: "💡", duration: 8000 }));
        }
      } else {
        toast.error(typeof detail === "string" ? detail : "Failed to connect");
      }
    } finally {
      setConnecting(false);
    }
  };

  const handleTest = async () => {
    setTesting(true);
    try {
      const resp = await garminAPI.testConnection();
      if (resp.data.is_connected) {
        toast.success(resp.data.message);
      } else {
        toast.error(resp.data.message);
      }
      loadGarminStatus();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Test failed");
    } finally {
      setTesting(false);
    }
  };

  const handleDisconnect = async () => {
    if (!window.confirm("Disconnect your Garmin account? Your stored credentials will be removed.")) return;
    try {
      await garminAPI.disconnect();
      toast.success("Garmin account disconnected");
      setGarminStatus(null);
      refreshUser();
    } catch {
      toast.error("Failed to disconnect");
    }
  };

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="font-display text-2xl font-bold text-gray-900 mb-6">Settings</h1>

      {/* Profile Info */}
      <div className="card mb-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold">Profile</h2>
          {!editingProfile && (
            <button onClick={() => setEditingProfile(true)} className="btn-secondary text-sm py-1 px-3">
              Edit
            </button>
          )}
        </div>

        {editingProfile ? (
          <form onSubmit={handleSaveProfile} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
              <input
                type="text"
                required
                className="input-field"
                value={profileName}
                onChange={(e) => setProfileName(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Profile Picture URL</label>
              <input
                type="url"
                className="input-field"
                value={profileAvatar}
                onChange={(e) => setProfileAvatar(e.target.value)}
                placeholder="https://example.com/your-photo.jpg"
              />
              <p className="text-xs text-gray-500 mt-1">Paste a URL to your profile picture</p>
              {profileAvatar && (
                <div className="mt-2">
                  <img src={profileAvatar} alt="Preview" className="w-16 h-16 rounded-full object-cover border border-gray-200" />
                </div>
              )}
            </div>
            {(user?.role === "coach" || user?.role === "admin") && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Venmo Link</label>
                <input
                  type="url"
                  className="input-field"
                  value={profileVenmo}
                  onChange={(e) => setProfileVenmo(e.target.value)}
                  placeholder="https://venmo.com/u/your-username"
                />
                <p className="text-xs text-gray-500 mt-1">Athletes will see this link to pay you</p>
              </div>
            )}
            <div className="flex gap-3">
              <button type="submit" disabled={savingProfile} className="btn-primary text-sm py-2">
                {savingProfile ? "Saving..." : "Save Changes"}
              </button>
              <button type="button" onClick={() => setEditingProfile(false)} className="btn-secondary text-sm py-2">
                Cancel
              </button>
            </div>
          </form>
        ) : (
          <div className="space-y-3 text-sm">
            {user?.avatar_url && (
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Photo</span>
                <img src={user.avatar_url} alt="Profile" className="w-10 h-10 rounded-full object-cover" />
              </div>
            )}
            <div className="flex justify-between">
              <span className="text-gray-600">Name</span>
              <span className="font-medium">{user?.full_name}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Email</span>
              <span className="font-medium">{user?.email}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Role</span>
              <span className="font-medium capitalize">{user?.role}</span>
            </div>
            {user?.venmo_link && (
              <div className="flex justify-between">
                <span className="text-gray-600">Venmo</span>
                <a href={user.venmo_link} target="_blank" rel="noopener noreferrer" className="text-dragonfly hover:underline">
                  Payment Link
                </a>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Garmin Connect */}
      {user?.role !== "admin" && (
        <div className="card">
          <h2 className="text-lg font-semibold mb-2">Garmin Connect</h2>
          <p className="text-sm text-gray-600 mb-4">
            Connect your Garmin account to sync workouts. Your credentials are encrypted and stored securely.
          </p>

          {/* How it works */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
            <h3 className="text-sm font-semibold text-blue-800 mb-2">How Garmin Integration Works</h3>
            <ol className="text-xs text-blue-700 space-y-1 list-decimal list-inside">
              <li>Enter your Garmin Connect email and password below</li>
              <li>We verify connectivity to your Garmin account immediately</li>
              <li>Your credentials are encrypted with AES-256 and stored securely</li>
              <li>
                {user?.role === "coach"
                  ? "Your workouts will appear in the Coach Dashboard for sharing"
                  : "Your coach can share workouts that you can import to your Garmin account"}
              </li>
              <li>You can disconnect at any time — credentials are permanently deleted</li>
            </ol>
            <p className="text-xs text-blue-600 mt-2">
              <strong>Note:</strong> Garmin does not offer a public OAuth API for workout management.
              We use the same authentication method as the official Garmin Connect app.
              Your password is never stored in plain text.
            </p>
          </div>

          {garminStatus?.is_connected ? (
            <div>
              <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
                <div className="flex items-center gap-2 text-green-700 font-medium text-sm">
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Connected to Garmin Connect
                </div>
                {garminStatus.garmin_email && (
                  <p className="text-sm text-green-600 mt-1">Account: {garminStatus.garmin_email}</p>
                )}
                {garminStatus.last_sync && (
                  <p className="text-xs text-green-500 mt-1">
                    Last verified: {new Date(garminStatus.last_sync).toLocaleString()}
                  </p>
                )}
              </div>
              <div className="flex gap-3">
                <button onClick={handleTest} disabled={testing} className="btn-secondary text-sm py-2">
                  {testing ? "Testing..." : "Test Connection"}
                </button>
                <button onClick={handleDisconnect} className="btn-danger text-sm py-2">
                  Disconnect
                </button>
              </div>
            </div>
          ) : (
            <form onSubmit={handleConnect} className="space-y-4">
              {garminStatus?.error_message && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
                  {garminStatus.error_message}
                </div>
              )}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Garmin Connect Email</label>
                <input
                  type="email"
                  required
                  className="input-field"
                  value={garminEmail}
                  onChange={(e) => setGarminEmail(e.target.value)}
                  placeholder="your-garmin-email@example.com"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Garmin Connect Password</label>
                <input
                  type="password"
                  required
                  className="input-field"
                  value={garminPassword}
                  onChange={(e) => setGarminPassword(e.target.value)}
                  placeholder="Your Garmin Connect password"
                />
              </div>
              <button type="submit" disabled={connecting} className="btn-primary w-full">
                {connecting ? "Connecting..." : "Connect Garmin Account"}
              </button>
            </form>
          )}
        </div>
      )}
    </div>
  );
};

export default SettingsPage;
