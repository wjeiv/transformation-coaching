import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "react-hot-toast";
import { AuthProvider, useAuth } from "./context/AuthContext";
import Layout from "./components/Layout";
import LandingPage from "./pages/LandingPage";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import AdminDashboard from "./pages/AdminDashboard";
import CoachDashboard from "./pages/CoachDashboard";
import AthleteDashboard from "./pages/AthleteDashboard";
import SettingsPage from "./pages/SettingsPage";

const ProtectedRoute: React.FC<{
  children: React.ReactNode;
  roles?: string[];
}> = ({ children, roles }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-dragonfly" />
      </div>
    );
  }

  if (!user) return <Navigate to="/login" replace />;
  if (roles && !roles.includes(user.role)) return <Navigate to="/" replace />;

  return <>{children}</>;
};

const HomeRedirect: React.FC = () => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-dragonfly" />
      </div>
    );
  }

  // Always show LandingPage for homepage ("/")
  return <LandingPage />;
};

const App: React.FC = () => {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: { borderRadius: "0.75rem", padding: "12px 16px", fontSize: "14px" },
          }}
        />
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<HomeRedirect />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />

            {/* Admin routes */}
            <Route
              path="/admin"
              element={
                <ProtectedRoute roles={["admin"]}>
                  <AdminDashboard />
                </ProtectedRoute>
              }
            />

            {/* Coach routes */}
            <Route
              path="/coach"
              element={
                <ProtectedRoute roles={["coach", "admin"]}>
                  <CoachDashboard />
                </ProtectedRoute>
              }
            />

            {/* Athlete routes */}
            <Route
              path="/athlete"
              element={
                <ProtectedRoute roles={["athlete"]}>
                  <AthleteDashboard />
                </ProtectedRoute>
              }
            />
            <Route
              path="/athlete/workouts"
              element={
                <ProtectedRoute roles={["athlete"]}>
                  <AthleteDashboard />
                </ProtectedRoute>
              }
            />

            {/* Settings (all authenticated users) */}
            <Route
              path="/settings"
              element={
                <ProtectedRoute>
                  <SettingsPage />
                </ProtectedRoute>
              }
            />

            {/* Catch-all */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
};

export default App;
