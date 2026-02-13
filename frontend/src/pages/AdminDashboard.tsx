import React, { useEffect, useState } from "react";
import { adminAPI } from "../services/api";
import toast from "react-hot-toast";

interface Stats {
  total_users: number;
  total_coaches: number;
  total_athletes: number;
  total_workouts_shared: number;
  total_contact_requests: number;
  recent_logins: any[];
}

interface UserItem {
  id: number;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  created_at: string;
  last_login: string | null;
  garmin_connected: boolean;
}

const AdminDashboard: React.FC = () => {
  const [stats, setStats] = useState<Stats | null>(null);
  const [users, setUsers] = useState<UserItem[]>([]);
  const [total, setTotal] = useState(0);
  const [roleFilter, setRoleFilter] = useState("");
  const [search, setSearch] = useState("");
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newUser, setNewUser] = useState({ email: "", password: "", full_name: "", role: "athlete" });
  const [creating, setCreating] = useState(false);

  const loadStats = async () => {
    try {
      const resp = await adminAPI.getStats();
      setStats(resp.data);
    } catch {
      toast.error("Failed to load stats");
    }
  };

  const loadUsers = async () => {
    try {
      const resp = await adminAPI.listUsers({
        role: roleFilter || undefined,
        search: search || undefined,
      });
      setUsers(resp.data.users);
      setTotal(resp.data.total);
    } catch {
      toast.error("Failed to load users");
    }
  };

  useEffect(() => { loadStats(); }, []);
  useEffect(() => { loadUsers(); }, [roleFilter, search]);

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreating(true);
    try {
      await adminAPI.createUser(newUser);
      toast.success("User created successfully");
      setShowCreateModal(false);
      setNewUser({ email: "", password: "", full_name: "", role: "athlete" });
      loadUsers();
      loadStats();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Failed to create user");
    } finally {
      setCreating(false);
    }
  };

  const handleToggleActive = async (user: UserItem) => {
    try {
      await adminAPI.updateUser(user.id, { is_active: !user.is_active });
      toast.success(`User ${user.is_active ? "deactivated" : "activated"}`);
      loadUsers();
    } catch {
      toast.error("Failed to update user");
    }
  };

  const handleDeleteUser = async (user: UserItem) => {
    if (!window.confirm(`Delete ${user.full_name}? This cannot be undone.`)) return;
    try {
      await adminAPI.deleteUser(user.id);
      toast.success("User deleted");
      loadUsers();
      loadStats();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Failed to delete user");
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="font-display text-2xl font-bold text-gray-900 mb-6">Admin Dashboard</h1>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
          {[
            { label: "Total Users", value: stats.total_users, color: "bg-blue-500" },
            { label: "Coaches", value: stats.total_coaches, color: "bg-green-500" },
            { label: "Athletes", value: stats.total_athletes, color: "bg-purple-500" },
            { label: "Workouts Shared", value: stats.total_workouts_shared, color: "bg-orange-500" },
            { label: "Contact Requests", value: stats.total_contact_requests, color: "bg-red-500" },
          ].map((s) => (
            <div key={s.label} className="card">
              <div className={`w-10 h-10 ${s.color} rounded-lg flex items-center justify-center text-white font-bold text-lg mb-2`}>
                {s.value}
              </div>
              <p className="text-sm text-gray-600">{s.label}</p>
            </div>
          ))}
        </div>
      )}

      {/* User Management */}
      <div className="card">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
          <h2 className="text-lg font-semibold">Users ({total})</h2>
          <div className="flex flex-wrap gap-2">
            <input
              type="text"
              placeholder="Search..."
              className="input-field text-sm py-2 w-48"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            <select
              className="input-field text-sm py-2 w-32"
              value={roleFilter}
              onChange={(e) => setRoleFilter(e.target.value)}
            >
              <option value="">All Roles</option>
              <option value="admin">Admin</option>
              <option value="coach">Coach</option>
              <option value="athlete">Athlete</option>
            </select>
            <button onClick={() => setShowCreateModal(true)} className="btn-primary text-sm py-2">
              + New User
            </button>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-3 px-2 font-medium text-gray-600">Name</th>
                <th className="text-left py-3 px-2 font-medium text-gray-600">Email</th>
                <th className="text-left py-3 px-2 font-medium text-gray-600">Role</th>
                <th className="text-left py-3 px-2 font-medium text-gray-600">Garmin</th>
                <th className="text-left py-3 px-2 font-medium text-gray-600">Last Login</th>
                <th className="text-left py-3 px-2 font-medium text-gray-600">Status</th>
                <th className="text-right py-3 px-2 font-medium text-gray-600">Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="py-3 px-2 font-medium">{u.full_name}</td>
                  <td className="py-3 px-2 text-gray-600">{u.email}</td>
                  <td className="py-3 px-2">
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                      u.role === "admin" ? "bg-red-100 text-red-700" :
                      u.role === "coach" ? "bg-green-100 text-green-700" :
                      "bg-blue-100 text-blue-700"
                    }`}>{u.role}</span>
                  </td>
                  <td className="py-3 px-2">
                    <span className={`text-xs ${u.garmin_connected ? "text-green-600" : "text-gray-400"}`}>
                      {u.garmin_connected ? "Connected" : "—"}
                    </span>
                  </td>
                  <td className="py-3 px-2 text-gray-500 text-xs">
                    {u.last_login ? new Date(u.last_login).toLocaleString() : "Never"}
                  </td>
                  <td className="py-3 px-2">
                    <span className={`text-xs font-medium ${u.is_active ? "text-green-600" : "text-red-600"}`}>
                      {u.is_active ? "Active" : "Inactive"}
                    </span>
                  </td>
                  <td className="py-3 px-2 text-right">
                    <button
                      onClick={() => handleToggleActive(u)}
                      className="text-xs text-gray-500 hover:text-gray-700 mr-2"
                    >
                      {u.is_active ? "Deactivate" : "Activate"}
                    </button>
                    <button
                      onClick={() => handleDeleteUser(u)}
                      className="text-xs text-red-500 hover:text-red-700"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Create User Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">Create New User</h3>
            <form onSubmit={handleCreateUser} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
                <input
                  type="text" required className="input-field"
                  value={newUser.full_name}
                  onChange={(e) => setNewUser({ ...newUser, full_name: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <input
                  type="email" required className="input-field"
                  value={newUser.email}
                  onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
                <input
                  type="password" required minLength={8} className="input-field"
                  value={newUser.password}
                  onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
                <select
                  className="input-field"
                  value={newUser.role}
                  onChange={(e) => setNewUser({ ...newUser, role: e.target.value })}
                >
                  <option value="athlete">Athlete</option>
                  <option value="coach">Coach</option>
                  <option value="admin">Admin</option>
                </select>
              </div>
              <div className="flex gap-3 pt-2">
                <button type="submit" disabled={creating} className="btn-primary flex-1">
                  {creating ? "Creating..." : "Create User"}
                </button>
                <button type="button" onClick={() => setShowCreateModal(false)} className="btn-secondary flex-1">
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminDashboard;
