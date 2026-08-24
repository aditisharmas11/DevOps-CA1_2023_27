import React, { useState } from 'react';
import { NavLink, useNavigate, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, 
  MessageSquare, 
  School, 
  Map, 
  Wrench, 
  Calendar, 
  BarChart3, 
  Activity, 
  Cpu, 
  LogOut, 
  Sun, 
  Moon, 
  Menu, 
  X,
  User,
  GraduationCap
} from 'lucide-react';

interface SidebarProps {
  darkMode: boolean;
  setDarkMode: (val: boolean) => void;
  user: { name: string; email: string; role: string } | null;
  onLogout: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ darkMode, setDarkMode, user, onLogout }) => {
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => {
    onLogout();
    navigate('/');
  };

  const navItems = [
    { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard, role: 'both' },
    { name: 'AI Copilot', path: '/copilot', icon: MessageSquare, role: 'both' },
    { name: 'Classrooms', path: '/classrooms', icon: School, role: 'both' },
    { name: 'Campus Map', path: '/map', icon: Map, role: 'both' },
    { name: 'Maintenance', path: '/maintenance', icon: Wrench, role: 'both' },
    { name: 'Events', path: '/events', icon: Calendar, role: 'both' },
  ];

  const adminItems = [
    { name: 'Analytics', path: '/admin', icon: BarChart3, role: 'admin' },
    { name: 'Occupancy', path: '/admin/occupancy', icon: Activity, role: 'admin' },
    { name: 'Sensors', path: '/admin/sensors', icon: Cpu, role: 'admin' },
  ];

  const filteredNavItems = navItems.filter(item => item.role === 'both' || item.role === user?.role);
  const showAdminMenu = user?.role === 'admin';

  return (
    <>
      {/* Desktop Sidebar (Left side) */}
      <aside className="hidden md:flex flex-col w-64 h-screen fixed left-0 top-0 bg-white dark:bg-dark-900 border-r border-slate-200/60 dark:border-slate-800/60 shadow-sm z-30 transition-all duration-300">
        {/* Brand Logo */}
        <div className="flex items-center gap-3 px-6 py-5 border-b border-slate-100 dark:border-slate-800">
          <div className="flex items-center justify-center w-10 h-10 rounded-xl gradient-primary text-white shadow-md shadow-brand-500/20">
            <GraduationCap size={22} className="animate-pulse-slow" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight bg-gradient-to-r from-brand-600 to-indigo-500 dark:from-brand-400 dark:to-indigo-300 bg-clip-text text-transparent">
              CampusIQ
            </h1>
            <p className="text-[10px] text-slate-400 font-medium tracking-wider uppercase">Think Smart</p>
          </div>
        </div>

        {/* User Card */}
        {user && (
          <div className="px-6 py-4 border-b border-slate-100 dark:border-slate-800">
            <div className="flex items-center gap-3">
              <div className="flex items-center justify-center w-10 h-10 rounded-full bg-indigo-50 dark:bg-dark-800 text-brand-600 dark:text-brand-400 border border-indigo-100/50 dark:border-dark-700">
                <User size={18} />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold truncate dark:text-slate-200">{user.name}</p>
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium capitalize bg-brand-50 dark:bg-dark-800 text-brand-700 dark:text-brand-300 border border-brand-100 dark:border-brand-900/30">
                  {user.role}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Navigation Items */}
        <nav className="flex-1 px-4 py-4 space-y-1.5 overflow-y-auto">
          {filteredNavItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.name}
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 ${
                    isActive
                      ? 'gradient-primary text-white shadow-md shadow-brand-500/15'
                      : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-dark-800 hover:text-slate-900 dark:hover:text-slate-200'
                  }`
                }
              >
                <Icon size={18} />
                <span>{item.name}</span>
              </NavLink>
            );
          })}

          {showAdminMenu && (
            <>
              <div className="pt-4 pb-2 px-4">
                <div className="h-[1px] bg-slate-100 dark:bg-slate-800 mb-2"></div>
                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Admin Dashboard</p>
              </div>
              {adminItems.map((item) => {
                const Icon = item.icon;
                return (
                  <NavLink
                    key={item.name}
                    to={item.path}
                    className={({ isActive }) =>
                      `flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 ${
                        isActive
                          ? 'gradient-primary text-white shadow-md shadow-brand-500/15'
                          : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-dark-800 hover:text-slate-900 dark:hover:text-slate-200'
                      }`
                    }
                  >
                    <Icon size={18} />
                    <span>{item.name}</span>
                  </NavLink>
                );
              })}
            </>
          )}
        </nav>

        {/* Footer controls (Dark theme & Logout) */}
        <div className="p-4 border-t border-slate-100 dark:border-slate-800 space-y-2">
          {/* Light/Dark Toggle */}
          <button
            onClick={() => setDarkMode(!darkMode)}
            className="flex items-center justify-between w-full px-4 py-2.5 rounded-xl text-sm font-medium text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-dark-800 transition-colors"
          >
            <div className="flex items-center gap-3">
              {darkMode ? <Sun size={18} /> : <Moon size={18} />}
              <span>{darkMode ? 'Light Mode' : 'Dark Mode'}</span>
            </div>
            <div className={`w-8 h-4 flex items-center rounded-full p-0.5 transition-colors duration-300 ${darkMode ? 'bg-brand-500' : 'bg-slate-300'}`}>
              <div className={`bg-white w-3 h-3 rounded-full shadow-md transform transition-transform duration-300 ${darkMode ? 'translate-x-4' : 'translate-x-0'}`}></div>
            </div>
          </button>

          {/* Logout Button */}
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 w-full px-4 py-2.5 rounded-xl text-sm font-medium text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/20 transition-colors"
          >
            <LogOut size={18} />
            <span>Logout</span>
          </button>
        </div>
      </aside>

      {/* Mobile Top Navbar & Menu */}
      <header className="md:hidden flex items-center justify-between w-full h-16 fixed top-0 left-0 bg-white dark:bg-dark-900 border-b border-slate-200/60 dark:border-slate-800/60 px-4 z-40 transition-colors duration-300">
        <div className="flex items-center gap-2">
          <div className="flex items-center justify-center w-8 h-8 rounded-lg gradient-primary text-white">
            <GraduationCap size={18} />
          </div>
          <span className="font-bold text-lg text-brand-600 dark:text-brand-400">CampusIQ</span>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setDarkMode(!darkMode)}
            className="p-2 rounded-lg text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-dark-800"
          >
            {darkMode ? <Sun size={18} /> : <Moon size={18} />}
          </button>
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="p-2 rounded-lg text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-dark-800"
          >
            {mobileOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
      </header>

      {/* Mobile Menu Overlay */}
      {mobileOpen && (
        <div className="md:hidden fixed inset-0 top-16 bg-white dark:bg-dark-950 z-40 flex flex-col p-6 animate-fade-in transition-colors duration-300">
          <nav className="flex-1 space-y-3">
            {filteredNavItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.name}
                  to={item.path}
                  onClick={() => setMobileOpen(false)}
                  className={({ isActive }) =>
                    `flex items-center gap-4 px-4 py-3.5 rounded-xl text-base font-semibold transition-all ${
                      isActive
                        ? 'gradient-primary text-white shadow-lg shadow-brand-500/20'
                        : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-dark-800'
                    }`
                  }
                >
                  <Icon size={20} />
                  <span>{item.name}</span>
                </NavLink>
              );
            })}

            {showAdminMenu && (
              <>
                <div className="pt-6 pb-2">
                  <div className="h-[1px] bg-slate-100 dark:bg-slate-800 mb-2"></div>
                  <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">Admin Pages</p>
                </div>
                {adminItems.map((item) => {
                  const Icon = item.icon;
                  return (
                    <NavLink
                      key={item.name}
                      to={item.path}
                      onClick={() => setMobileOpen(false)}
                      className={({ isActive }) =>
                        `flex items-center gap-4 px-4 py-3.5 rounded-xl text-base font-semibold transition-all ${
                          isActive
                            ? 'gradient-primary text-white shadow-lg shadow-brand-500/20'
                            : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-dark-800'
                        }`
                      }
                    >
                      <Icon size={20} />
                      <span>{item.name}</span>
                    </NavLink>
                  );
                })}
              </>
            )}
          </nav>

          <div className="pt-6 border-t border-slate-100 dark:border-slate-800">
            <button
              onClick={handleLogout}
              className="flex items-center justify-center gap-3 w-full py-3.5 bg-red-50 dark:bg-red-950/20 text-red-600 dark:text-red-400 rounded-xl font-bold transition-all"
            >
              <LogOut size={20} />
              <span>Logout</span>
            </button>
          </div>
        </div>
      )}

      {/* Mobile Bottom Navigation (Always visible for quick actions) */}
      <nav className="md:hidden fixed bottom-0 left-0 w-full bg-white dark:bg-dark-900 border-t border-slate-200/60 dark:border-slate-800/60 h-16 flex items-center justify-around px-2 z-35 transition-colors duration-300">
        <NavLink
          to="/dashboard"
          className={({ isActive }) =>
            `flex flex-col items-center justify-center w-12 h-12 rounded-xl transition-colors ${
              isActive ? 'text-brand-600 dark:text-brand-400' : 'text-slate-400 hover:text-slate-600 dark:hover:text-slate-200'
            }`
          }
        >
          <LayoutDashboard size={20} />
          <span className="text-[9px] font-bold mt-0.5">Home</span>
        </NavLink>
        <NavLink
          to="/map"
          className={({ isActive }) =>
            `flex flex-col items-center justify-center w-12 h-12 rounded-xl transition-colors ${
              isActive ? 'text-brand-600 dark:text-brand-400' : 'text-slate-400 hover:text-slate-600 dark:hover:text-slate-200'
            }`
          }
        >
          <Map size={20} />
          <span className="text-[9px] font-bold mt-0.5">Map</span>
        </NavLink>
        <NavLink
          to="/copilot"
          className={({ isActive }) =>
            `flex flex-col items-center justify-center w-12 h-12 rounded-xl transition-colors ${
              isActive ? 'text-brand-600 dark:text-brand-400' : 'text-slate-400 hover:text-slate-600 dark:hover:text-slate-200'
            }`
          }
        >
          <MessageSquare size={20} />
          <span className="text-[9px] font-bold mt-0.5">Copilot</span>
        </NavLink>
        <NavLink
          to="/events"
          className={({ isActive }) =>
            `flex flex-col items-center justify-center w-12 h-12 rounded-xl transition-colors ${
              isActive ? 'text-brand-600 dark:text-brand-400' : 'text-slate-400 hover:text-slate-600 dark:hover:text-slate-200'
            }`
          }
        >
          <Calendar size={20} />
          <span className="text-[9px] font-bold mt-0.5">Events</span>
        </NavLink>
      </nav>
    </>
  );
};

export default Sidebar;
