import React, { Fragment, useState } from "react";
import { Link, Outlet, useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { APP_VERSION, BUILD_DATE } from "../version";

const Logo: React.FC<{ className?: string }> = ({ className }) => (
  <img src="/coach-trans1.png" alt="Transformation Coaching" className={className} />
);

const Layout: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  const navLinks = () => {
    if (!user) return [];
    switch (user.role) {
      case "admin":
        return [
          { to: "/", label: "Home" },
          { to: "/admin", label: "Dashboard" },
          { to: "/settings", label: "Settings" },
        ];
      case "coach":
        return [
          { to: "/", label: "Home" },
          { to: "/coach", label: "Dashboard" },
          { to: "/settings", label: "Settings" },
        ];
      case "athlete":
        return [
          { to: "/", label: "Home" },
          { to: "/athlete", label: "Dashboard" },
          { to: "/athlete/workouts", label: "My Workouts" },
          { to: "/settings", label: "Settings" },
        ];
      default:
        return [];
    }
  };

  const isActive = (path: string) => location.pathname === path;

  return (
    <div className="min-h-screen flex flex-col">
      <nav className="bg-white border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Link to="/" className="flex items-center gap-2 text-dragonfly hover:text-dragonfly-dark transition-colors">
                <Logo className="h-8 w-8" />
                <span className="font-display font-bold text-lg hidden sm:block">
                  Transformation Coaching
                </span>
              </Link>
              {user && (
                <div className="hidden md:flex ml-8 gap-1">
                  {navLinks().map((link) => (
                    <Link
                      key={link.to}
                      to={link.to}
                      className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                        isActive(link.to)
                          ? "bg-dragonfly/10 text-dragonfly"
                          : "text-gray-600 hover:text-gray-900 hover:bg-gray-100"
                      }`}
                    >
                      {link.label}
                    </Link>
                  ))}
                </div>
              )}
            </div>

            <div className="flex items-center gap-3">
              {user ? (
                <>
                  <div className="hidden sm:flex items-center gap-2">
                    {user.avatar_url && (
                      <img 
                        src={user.avatar_url} 
                        alt={user.full_name}
                        className="w-8 h-8 rounded-full object-cover border border-gray-200"
                      />
                    )}
                    <span className="text-sm text-gray-600">
                      {user.full_name}
                      <span className="ml-1 text-xs px-2 py-0.5 rounded-full bg-dragonfly/10 text-dragonfly font-medium">
                        {user.role}
                      </span>
                    </span>
                  </div>
                  <button onClick={handleLogout} className="btn-secondary text-xs py-2 px-3">
                    Logout
                  </button>
                </>
              ) : (
                <>
                  <Link to="/login" className="btn-secondary text-xs py-2 px-3">
                    Login
                  </Link>
                  <Link to="/register" className="btn-primary text-xs py-2 px-3">
                    Get Started
                  </Link>
                </>
              )}

              {/* Mobile menu button */}
              {user && (
                <button
                  onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                  className="md:hidden p-2 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100"
                >
                  <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    {mobileMenuOpen ? (
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    ) : (
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                    )}
                  </svg>
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Mobile menu */}
        {mobileMenuOpen && user && (
          <div className="md:hidden border-t border-gray-200 bg-white">
            <div className="px-4 py-3 space-y-1">
              <div className="flex items-center gap-2 text-sm text-gray-600 pb-2 border-b border-gray-100 mb-2">
                {user.avatar_url && (
                  <img 
                    src={user.avatar_url} 
                    alt={user.full_name}
                    className="w-6 h-6 rounded-full object-cover border border-gray-200"
                  />
                )}
                <span>{user.full_name} ({user.role})</span>
              </div>
              {navLinks().map((link) => (
                <Link
                  key={link.to}
                  to={link.to}
                  onClick={() => setMobileMenuOpen(false)}
                  className={`block px-3 py-2 rounded-md text-sm font-medium ${
                    isActive(link.to)
                      ? "bg-dragonfly/10 text-dragonfly"
                      : "text-gray-600 hover:bg-gray-100"
                  }`}
                >
                  {link.label}
                </Link>
              ))}
            </div>
          </div>
        )}
      </nav>

      <main className="flex-1">
        <Outlet />
      </main>

      <footer className="bg-gray-900 text-gray-400 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col sm:flex-row justify-between items-center gap-4">
            <div className="flex items-center gap-2 text-white">
              <Logo className="h-6 w-6" />
              <span className="font-display font-semibold">Transformation Coaching</span>
            </div>
            <div className="flex flex-col sm:flex-row items-center gap-2 sm:gap-4 text-sm">
              <span>v{APP_VERSION}</span>
              <span>Built: {BUILD_DATE}</span>
              <span>&copy; 2026 Transformation Coaching. All rights reserved.</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Layout;
