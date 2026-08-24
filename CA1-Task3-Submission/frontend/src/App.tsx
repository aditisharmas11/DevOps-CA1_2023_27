import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import LandingPage from './pages/LandingPage';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Copilot from './pages/Copilot';
import Classrooms from './pages/Classrooms';
import CampusMap from './pages/CampusMap';
import Maintenance from './pages/Maintenance';
import Events from './pages/Events';
import AdminDashboard from './pages/AdminDashboard';

// Type definition for user state
interface User {
  id: number;
  email: string;
  name: string;
  role: string;
}

const AppContent: React.FC = () => {
  const [darkMode, setDarkMode] = useState<boolean>(() => {
    return localStorage.getItem('theme') === 'dark';
  });

  const [user, setUser] = useState<User | null>(() => {
    const savedUser = localStorage.getItem('user');
    return savedUser ? JSON.parse(savedUser) : null;
  });

  const location = useLocation();

  // Apply dark mode theme class to document body
  useEffect(() => {
    if (darkMode) {
      document.body.classList.add('dark');
      localStorage.setItem('theme', 'dark');
    } else {
      document.body.classList.remove('dark');
      localStorage.setItem('theme', 'light');
    }
  }, [darkMode]);

  const handleLogin = (loggedUser: User) => {
    setUser(loggedUser);
    localStorage.setItem('user', JSON.stringify(loggedUser));
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem('user');
  };

  // Determine if we should show the sidebar layout
  // Landing and Login pages should not show the sidebar
  const isAuthPage = location.pathname === '/' || location.pathname === '/login';

  // Guard for protected routes
  const RequireAuth: React.FC<{ children: React.ReactNode; allowedRole?: string }> = ({ children, allowedRole }) => {
    if (!user) {
      return <Navigate to="/login" replace />;
    }
    if (allowedRole && user.role !== allowedRole) {
      return <Navigate to="/dashboard" replace />;
    }
    return <>{children}</>;
  };

  return (
    <div className="min-h-screen flex flex-col md:flex-row transition-colors duration-300">
      {!isAuthPage && (
        <Sidebar 
          darkMode={darkMode} 
          setDarkMode={setDarkMode} 
          user={user} 
          onLogout={handleLogout} 
        />
      )}
      
      <main className={`flex-1 flex flex-col ${!isAuthPage ? 'md:pl-64 pt-16 md:pt-0 pb-16 md:pb-0' : ''}`}>
        <Routes>
          {/* Public Routes */}
          <Route path="/" element={user ? <Navigate to="/dashboard" replace /> : <LandingPage />} />
          <Route path="/login" element={user ? <Navigate to="/dashboard" replace /> : <Login onLogin={handleLogin} />} />
          
          {/* User Protected Routes */}
          <Route path="/dashboard" element={<RequireAuth><Dashboard user={user} /></RequireAuth>} />
          <Route path="/copilot" element={<RequireAuth><Copilot /></RequireAuth>} />
          <Route path="/classrooms" element={<RequireAuth><Classrooms /></RequireAuth>} />
          <Route path="/map" element={<RequireAuth><CampusMap /></RequireAuth>} />
          <Route path="/maintenance" element={<RequireAuth><Maintenance user={user} /></RequireAuth>} />
          <Route path="/events" element={<RequireAuth><Events /></RequireAuth>} />
          
          {/* Admin Protected Routes */}
          <Route path="/admin" element={<RequireAuth allowedRole="admin"><AdminDashboard user={user} activeTab="analytics" /></RequireAuth>} />
          <Route path="/admin/occupancy" element={<RequireAuth allowedRole="admin"><AdminDashboard user={user} activeTab="occupancy" /></RequireAuth>} />
          <Route path="/admin/sensors" element={<RequireAuth allowedRole="admin"><AdminDashboard user={user} activeTab="sensors" /></RequireAuth>} />

          {/* Catch-all Redirect */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
};

const App: React.FC = () => {
  return (
    <Router>
      <AppContent />
    </Router>
  );
};

export default App;
