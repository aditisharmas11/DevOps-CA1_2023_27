import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { 
  GraduationCap, 
  Mail, 
  Lock, 
  ArrowLeft,
  AlertCircle,
  Loader2,
  CheckCircle2,
  ChevronRight
} from 'lucide-react';
import api from '../services/api';

interface LoginProps {
  onLogin: (user: { id: number; email: string; name: string; role: string }) => void;
}

const Login: React.FC<LoginProps> = ({ onLogin }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleDemoFill = (demoEmail: string, demoPass: string) => {
    setEmail(demoEmail);
    setPassword(demoPass);
    setError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setError('Please fill in all fields.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await api.post('/login', { email, password });
      onLogin(response.data);
      navigate('/dashboard');
    } catch (err: any) {
      if (err.response && err.response.data && err.response.data.error) {
        setError(err.response.data.error);
      } else {
        setError('Connection failed. Please ensure the backend is running.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen bg-slate-50 dark:bg-dark-950 flex flex-col justify-center py-12 sm:px-6 lg:px-8 overflow-hidden">
      {/* Glow Blurs */}
      <div className="absolute top-1/4 left-1/4 w-[300px] h-[300px] rounded-full bg-brand-500/10 dark:bg-brand-500/5 blur-[80px] pointer-events-none"></div>
      <div className="absolute bottom-1/4 right-1/4 w-[300px] h-[300px] rounded-full bg-indigo-500/10 dark:bg-indigo-500/5 blur-[80px] pointer-events-none"></div>

      <div className="sm:mx-auto sm:w-full sm:max-w-md z-10 px-4">
        {/* Back Link */}
        <Link 
          to="/" 
          className="inline-flex items-center gap-1.5 text-xs font-bold text-slate-500 dark:text-slate-400 hover:text-brand-600 dark:hover:text-brand-400 transition-colors uppercase tracking-wider mb-6"
        >
          <ArrowLeft size={14} />
          <span>Back to Home</span>
        </Link>

        {/* Brand */}
        <div className="flex items-center gap-3 justify-center mb-6">
          <div className="flex items-center justify-center w-12 h-12 rounded-2xl gradient-primary text-white shadow-lg shadow-brand-500/25">
            <GraduationCap size={26} />
          </div>
          <span className="font-extrabold text-3xl text-slate-800 dark:text-white tracking-tight">
            Campus<span className="text-brand-600 dark:text-brand-400">IQ</span>
          </span>
        </div>

        <h2 className="text-center text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
          Sign in to your account
        </h2>
        <p className="mt-1.5 text-center text-sm text-slate-500 dark:text-slate-400">
          Enter credentials or use a preconfigured demo account.
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md z-10 px-4">
        <div className="glass-panel p-6 sm:p-8 rounded-3xl shadow-lg border border-slate-200/50 dark:border-slate-800/40">
          {error && (
            <div className="mb-5 p-4 bg-red-50 dark:bg-red-950/20 border border-red-200/60 dark:border-red-950/30 rounded-2xl flex items-start gap-3">
              <AlertCircle className="text-red-500 dark:text-red-400 shrink-0 mt-0.5" size={18} />
              <p className="text-sm font-semibold text-red-700 dark:text-red-400">{error}</p>
            </div>
          )}

          <form className="space-y-5" onSubmit={handleSubmit}>
            {/* Email Field */}
            <div>
              <label htmlFor="email" className="block text-xs font-bold text-slate-600 dark:text-slate-400 uppercase tracking-wider mb-1.5">
                Email Address
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-slate-400 dark:text-slate-500">
                  <Mail size={18} />
                </div>
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="student@campusiq.com"
                  className="block w-full pl-11 pr-4 py-3 bg-white dark:bg-dark-900 border border-slate-200 dark:border-slate-800 rounded-2xl text-sm placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-500 dark:focus:ring-brand-500 focus:border-transparent dark:text-slate-100 transition-all shadow-sm"
                />
              </div>
            </div>

            {/* Password Field */}
            <div>
              <label htmlFor="password" className="block text-xs font-bold text-slate-600 dark:text-slate-400 uppercase tracking-wider mb-1.5">
                Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-slate-400 dark:text-slate-500">
                  <Lock size={18} />
                </div>
                <input
                  id="password"
                  name="password"
                  type="password"
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="block w-full pl-11 pr-4 py-3 bg-white dark:bg-dark-900 border border-slate-200 dark:border-slate-800 rounded-2xl text-sm placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-500 dark:focus:ring-brand-500 focus:border-transparent dark:text-slate-100 transition-all shadow-sm"
                />
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full inline-flex items-center justify-center gap-2 px-6 py-3.5 rounded-2xl font-bold text-white gradient-primary shadow-md shadow-brand-500/20 hover:shadow-lg hover:shadow-brand-500/35 transition-all disabled:opacity-50"
            >
              {loading ? (
                <>
                  <Loader2 className="animate-spin" size={18} />
                  <span>Verifying credentials...</span>
                </>
              ) : (
                <>
                  <span>Sign In</span>
                  <ChevronRight size={18} />
                </>
              )}
            </button>
          </form>

          {/* Quick Demo Logins Section */}
          <div className="mt-8 pt-6 border-t border-slate-100 dark:border-slate-800">
            <h4 className="text-xs font-extrabold text-slate-400 uppercase tracking-wider mb-3">
              Demo Access Credentials
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {/* Student Card */}
              <button
                type="button"
                onClick={() => handleDemoFill('student@campusiq.com', 'student123')}
                className="flex items-center gap-3 p-3 text-left rounded-2xl border border-indigo-100 dark:border-dark-800/40 bg-indigo-50/20 dark:bg-dark-900/40 hover:bg-indigo-50/50 dark:hover:bg-dark-800/50 transition-all group"
              >
                <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-indigo-100 dark:bg-dark-800 text-indigo-600 dark:text-indigo-400 group-hover:scale-95 transition-all">
                  <CheckCircle2 size={16} />
                </div>
                <div className="min-w-0">
                  <p className="text-xs font-bold text-slate-800 dark:text-slate-200">Student Account</p>
                  <p className="text-[10px] text-slate-400 font-medium truncate">student@campusiq.com</p>
                </div>
              </button>

              {/* Admin Card */}
              <button
                type="button"
                onClick={() => handleDemoFill('admin@campusiq.com', 'admin123')}
                className="flex items-center gap-3 p-3 text-left rounded-2xl border border-purple-100 dark:border-dark-800/40 bg-purple-50/20 dark:bg-dark-900/40 hover:bg-purple-50/50 dark:hover:bg-dark-800/50 transition-all group"
              >
                <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-purple-100 dark:bg-dark-800 text-purple-600 dark:text-purple-400 group-hover:scale-95 transition-all">
                  <CheckCircle2 size={16} />
                </div>
                <div className="min-w-0">
                  <p className="text-xs font-bold text-slate-800 dark:text-slate-200">Admin Account</p>
                  <p className="text-[10px] text-slate-400 font-medium truncate">admin@campusiq.com</p>
                </div>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
