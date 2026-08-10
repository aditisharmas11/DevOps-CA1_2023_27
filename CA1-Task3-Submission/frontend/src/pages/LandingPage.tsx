import React from 'react';
import { Link } from 'react-router-dom';
import { 
  MessageSquare, 
  School, 
  Wrench, 
  BarChart3, 
  ArrowRight,
  GraduationCap,
  Sparkles,
  ShieldCheck,
  Zap
} from 'lucide-react';

const LandingPage: React.FC = () => {
  const features = [
    {
      icon: MessageSquare,
      title: 'AI Campus Copilot',
      desc: 'Ask natural-language questions about classroom details, locations, events, or report broken equipment instantly.',
      color: 'from-blue-500 to-indigo-500',
      badge: 'Powered by Qwen'
    },
    {
      icon: School,
      title: 'Smart Classrooms',
      desc: 'Check live classroom occupancies, projector/AC statuses, and receive smart recommendations for empty study spaces.',
      color: 'from-emerald-500 to-teal-500',
      badge: 'Live Telemetry'
    },
    {
      icon: Wrench,
      title: 'Smart Maintenance',
      desc: 'Report issues directly. AI automatically classifies issue type, priority levels, and logs it into the queue.',
      color: 'from-rose-500 to-orange-500',
      badge: 'Auto-Triage'
    },
    {
      icon: BarChart3,
      title: 'Campus Analytics',
      desc: 'Monitor occupancy charts, classroom utilization indices, and simulated IoT sensor logs from an admin dashboard.',
      color: 'from-purple-500 to-pink-500',
      badge: 'Recharts Visuals'
    }
  ];

  return (
    <div className="relative min-h-screen bg-slate-50 dark:bg-dark-950 overflow-hidden flex flex-col justify-between">
      {/* Decorative Blur Backdrops */}
      <div className="absolute top-[-20%] left-[-10%] w-[500px] h-[500px] rounded-full bg-brand-500/10 dark:bg-brand-500/5 blur-[120px] pointer-events-none"></div>
      <div className="absolute bottom-[-10%] right-[-10%] w-[600px] h-[600px] rounded-full bg-indigo-500/10 dark:bg-indigo-500/5 blur-[150px] pointer-events-none"></div>

      {/* Header / Nav */}
      <header className="max-w-7xl mx-auto w-full px-6 py-6 flex items-center justify-between z-10">
        <div className="flex items-center gap-2">
          <div className="flex items-center justify-center w-10 h-10 rounded-xl gradient-primary text-white shadow-lg shadow-brand-500/20">
            <GraduationCap size={22} />
          </div>
          <span className="font-extrabold text-2xl text-slate-800 dark:text-white tracking-tight">
            Campus<span className="text-brand-600 dark:text-brand-400">IQ</span>
          </span>
        </div>
        <Link 
          to="/login" 
          className="px-5 py-2.5 rounded-xl font-semibold text-sm text-slate-700 dark:text-slate-200 bg-white dark:bg-dark-900 border border-slate-200/80 dark:border-slate-800 shadow-sm hover:shadow-md hover:bg-slate-50 dark:hover:bg-dark-800 transition-all"
        >
          Sign In
        </Link>
      </header>

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto w-full px-6 py-12 md:py-20 text-center z-10 flex-1 flex flex-col justify-center">
        {/* Glow Tagline */}
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-brand-50 dark:bg-brand-950/40 border border-brand-100 dark:border-brand-900/30 text-brand-700 dark:text-brand-400 text-xs font-bold uppercase tracking-wider mb-6 mx-auto animate-bounce-slow">
          <Sparkles size={14} />
          <span>Think Smart. Campus Smarter.</span>
        </div>

        {/* Hero Title */}
        <h1 className="text-4xl sm:text-6xl md:text-7xl font-extrabold tracking-tight text-slate-900 dark:text-white mb-6">
          Meet <span className="bg-gradient-to-r from-brand-600 via-indigo-500 to-purple-500 bg-clip-text text-transparent">CampusIQ</span>
        </h1>

        {/* Hero Subtitle */}
        <p className="max-w-2xl mx-auto text-lg sm:text-xl text-slate-600 dark:text-slate-300 mb-10 leading-relaxed font-medium">
          An AI-powered assistant that makes your campus smarter, more connected, and easier to navigate. Get classroom finders, maintenance reports, and maps, all in one place.
        </p>

        {/* Call to Actions */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 max-w-md mx-auto mb-16 sm:mb-24">
          <Link
            to="/login"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-8 py-4 rounded-2xl font-bold text-white gradient-primary shadow-lg shadow-brand-500/20 hover:shadow-xl hover:shadow-brand-500/30 transition-all hover:scale-[1.02]"
          >
            <span>Get Started</span>
            <ArrowRight size={18} />
          </Link>
          <Link
            to="/login"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-8 py-4 rounded-2xl font-bold text-slate-800 dark:text-white bg-white dark:bg-dark-900 border border-slate-200/80 dark:border-slate-800 shadow-sm hover:bg-slate-50 dark:hover:bg-dark-800 transition-all hover:scale-[1.02]"
          >
            <span>Try AI Copilot</span>
          </Link>
        </div>

        {/* Feature Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 text-left">
          {features.map((feat, index) => {
            const Icon = feat.icon;
            return (
              <div 
                key={index} 
                className="group relative rounded-3xl p-6 glass-panel glass-card-hover hover:border-brand-500/20 shadow-sm"
              >
                {/* Glow bar */}
                <div className={`absolute top-0 left-0 w-full h-1.5 rounded-t-3xl bg-gradient-to-r ${feat.color}`}></div>
                
                {/* Icon box */}
                <div className={`w-12 h-12 rounded-2xl bg-gradient-to-br ${feat.color} text-white flex items-center justify-center mb-5 shadow-md`}>
                  <Icon size={24} />
                </div>
                
                {/* Content */}
                <div className="flex items-center gap-2 mb-2">
                  <h3 className="font-bold text-lg text-slate-800 dark:text-slate-100 group-hover:text-brand-600 dark:group-hover:text-brand-400 transition-colors">
                    {feat.title}
                  </h3>
                </div>
                <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed mb-4">
                  {feat.desc}
                </p>
                <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-bold tracking-wide uppercase bg-slate-100 dark:bg-dark-800 text-slate-600 dark:text-slate-400">
                  {feat.badge}
                </span>
              </div>
            );
          })}
        </div>
      </section>

      {/* Footer */}
      <footer className="max-w-7xl mx-auto w-full px-6 py-8 border-t border-slate-200/40 dark:border-slate-800/40 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-400 font-medium z-10">
        <p>© 2026 CampusIQ. All rights reserved.</p>
        <div className="flex items-center gap-6 mt-4 sm:mt-0">
          <a href="#" className="hover:text-slate-600 dark:hover:text-white transition-colors">Terms of Service</a>
          <a href="#" className="hover:text-slate-600 dark:hover:text-white transition-colors">Privacy Policy</a>
          <a href="#" className="hover:text-slate-600 dark:hover:text-white transition-colors">Security</a>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
