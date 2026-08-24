import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  MessageSquare, 
  School, 
  Wrench, 
  Map, 
  Calendar, 
  ArrowRight,
  Sparkles,
  Users,
  Activity,
  AlertTriangle,
  Loader2,
  Clock,
  MapPin
} from 'lucide-react';
import api from '../services/api';

interface DashboardProps {
  user: { name: string; email: string; role: string } | null;
}

const Dashboard: React.FC<DashboardProps> = ({ user }) => {
  const [stats, setStats] = useState({
    availableClassrooms: 18,
    occupancy: 67,
    openIssues: 12,
    todayEventsCount: 5
  });
  const [events, setEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        // Fetch classrooms
        const roomsRes = await api.get('/classrooms');
        const available = roomsRes.data.filter((r: any) => r.status === 'AVAILABLE').length;

        // Fetch occupancy
        const occRes = await api.get('/occupancy');
        const avgOcc = occRes.data.length > 0
          ? Math.round(occRes.data.reduce((acc: number, item: any) => acc + item.occupancy_pct, 0) / occRes.data.length)
          : 67;

        // Fetch maintenance tickets
        const maintRes = await api.get('/maintenance');
        const open = maintRes.data.filter((t: any) => t.status !== 'RESOLVED').length;

        // Fetch events
        const eventsRes = await api.get('/events');
        const todayStr = new Date().toISOString().split('T')[0];
        
        // Filter events for today or future events
        const todayEvents = eventsRes.data.filter((e: any) => e.date === todayStr);
        const sortedEvents = eventsRes.data
          .filter((e: any) => e.date >= todayStr)
          .slice(0, 3); // show top 3 upcoming

        setStats({
          availableClassrooms: available,
          occupancy: avgOcc,
          openIssues: open,
          todayEventsCount: todayEvents.length
        });
        setEvents(sortedEvents);
      } catch (err) {
        console.error('Error fetching dashboard statistics:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  // Determine greeting based on local time
  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good Morning 👋';
    if (hour < 17) return 'Good Afternoon 👋';
    return 'Good Evening 👋';
  };

  return (
    <div className="flex-1 min-h-screen bg-slate-50/50 dark:bg-dark-950 p-6 md:p-8 space-y-8">
      {/* Header section */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <p className="text-xs font-bold text-brand-600 dark:text-brand-400 uppercase tracking-wider mb-1">
            Student Portal
          </p>
          <h2 className="text-3xl font-extrabold tracking-tight text-slate-800 dark:text-white">
            {getGreeting()}
          </h2>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
            Welcome back, <span className="font-bold text-slate-700 dark:text-slate-200">{user?.name}</span>. Here is what's happening on your campus today.
          </p>
        </div>
        
        {/* Active Copilot floating badge */}
        <Link 
          to="/copilot" 
          className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-brand-600 to-indigo-500 text-white rounded-xl font-bold text-xs shadow-md shadow-brand-500/15 hover:shadow-lg transition-all animate-pulse-slow hover:scale-105"
        >
          <Sparkles size={14} />
          <span>Ask Copilot Anything</span>
        </Link>
      </div>

      {loading ? (
        <div className="h-[400px] flex items-center justify-center">
          <Loader2 className="animate-spin text-brand-500" size={32} />
        </div>
      ) : (
        <>
          {/* Stats Grid */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
            {/* Stat Card 1 */}
            <div className="glass-panel p-5 rounded-3xl shadow-sm border border-slate-200/50 dark:border-slate-800/40 relative overflow-hidden group hover:border-brand-500/20 transition-all">
              <div className="absolute top-4 right-4 text-emerald-500 bg-emerald-50 dark:bg-emerald-950/20 p-2.5 rounded-2xl">
                <School size={20} />
              </div>
              <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">Available Classrooms</p>
              <h3 className="text-3xl font-black text-slate-800 dark:text-slate-100 mt-2">{stats.availableClassrooms}</h3>
              <p className="text-[10px] text-slate-400 font-bold mt-1">Status: READY FOR BOOKING</p>
            </div>

            {/* Stat Card 2 */}
            <div className="glass-panel p-5 rounded-3xl shadow-sm border border-slate-200/50 dark:border-slate-800/40 relative overflow-hidden group hover:border-brand-500/20 transition-all">
              <div className="absolute top-4 right-4 text-brand-500 bg-brand-50 dark:bg-brand-950/20 p-2.5 rounded-2xl">
                <Activity size={20} />
              </div>
              <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">Campus Occupancy</p>
              <h3 className="text-3xl font-black text-slate-800 dark:text-slate-100 mt-2">{stats.occupancy}%</h3>
              <div className="w-full bg-slate-100 dark:bg-dark-800 rounded-full h-1.5 mt-3 overflow-hidden">
                <div className="gradient-primary h-full rounded-full" style={{ width: `${stats.occupancy}%` }}></div>
              </div>
            </div>

            {/* Stat Card 3 */}
            <div className="glass-panel p-5 rounded-3xl shadow-sm border border-slate-200/50 dark:border-slate-800/40 relative overflow-hidden group hover:border-brand-500/20 transition-all">
              <div className="absolute top-4 right-4 text-amber-500 bg-amber-50 dark:bg-amber-950/20 p-2.5 rounded-2xl">
                <AlertTriangle size={20} />
              </div>
              <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">Open Issues</p>
              <h3 className="text-3xl font-black text-slate-800 dark:text-slate-100 mt-2">{stats.openIssues}</h3>
              <p className="text-[10px] text-slate-400 font-bold mt-1">Pending Resolution</p>
            </div>

            {/* Stat Card 4 */}
            <div className="glass-panel p-5 rounded-3xl shadow-sm border border-slate-200/50 dark:border-slate-800/40 relative overflow-hidden group hover:border-brand-500/20 transition-all">
              <div className="absolute top-4 right-4 text-purple-500 bg-purple-50 dark:bg-purple-950/20 p-2.5 rounded-2xl">
                <Calendar size={20} />
              </div>
              <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">Today's Events</p>
              <h3 className="text-3xl font-black text-slate-800 dark:text-slate-100 mt-2">{stats.todayEventsCount}</h3>
              <p className="text-[10px] text-slate-400 font-bold mt-1">Scheduled for Today</p>
            </div>
          </div>

          {/* Quick Actions & Events Split */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            
            {/* Quick Actions Column */}
            <div className="lg:col-span-2 space-y-6">
              <h4 className="text-sm font-extrabold text-slate-400 uppercase tracking-wider">Quick Actions</h4>
              
              <div className="grid grid-cols-2 gap-4">
                {/* Copilot */}
                <Link 
                  to="/copilot"
                  className="flex flex-col items-start p-6 rounded-3xl glass-panel glass-card-hover border border-slate-200/40 dark:border-slate-800/30 text-left group"
                >
                  <div className="p-3 bg-indigo-500/10 text-brand-600 dark:text-brand-400 rounded-2xl mb-4 group-hover:scale-105 transition-all">
                    <MessageSquare size={24} />
                  </div>
                  <h5 className="font-bold text-lg text-slate-800 dark:text-slate-100">AI Copilot</h5>
                  <p className="text-xs text-slate-400 mt-1">Query classrooms, locations, events, or report issues.</p>
                </Link>

                {/* Find Classroom */}
                <Link 
                  to="/classrooms"
                  className="flex flex-col items-start p-6 rounded-3xl glass-panel glass-card-hover border border-slate-200/40 dark:border-slate-800/30 text-left group"
                >
                  <div className="p-3 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 rounded-2xl mb-4 group-hover:scale-105 transition-all">
                    <School size={24} />
                  </div>
                  <h5 className="font-bold text-lg text-slate-800 dark:text-slate-100">Find Classroom</h5>
                  <p className="text-xs text-slate-400 mt-1">Check availability, equipment list, or recommendations.</p>
                </Link>

                {/* Report Issue */}
                <Link 
                  to="/maintenance"
                  className="flex flex-col items-start p-6 rounded-3xl glass-panel glass-card-hover border border-slate-200/40 dark:border-slate-800/30 text-left group"
                >
                  <div className="p-3 bg-rose-500/10 text-rose-600 dark:text-rose-400 rounded-2xl mb-4 group-hover:scale-105 transition-all">
                    <Wrench size={24} />
                  </div>
                  <h5 className="font-bold text-lg text-slate-800 dark:text-slate-100">Report Issue</h5>
                  <p className="text-xs text-slate-400 mt-1">File a maintenance ticket. Auto priority classification.</p>
                </Link>

                {/* Campus Map */}
                <Link 
                  to="/map"
                  className="flex flex-col items-start p-6 rounded-3xl glass-panel glass-card-hover border border-slate-200/40 dark:border-slate-800/30 text-left group"
                >
                  <div className="p-3 bg-amber-500/10 text-amber-600 dark:text-amber-400 rounded-2xl mb-4 group-hover:scale-105 transition-all">
                    <Map size={24} />
                  </div>
                  <h5 className="font-bold text-lg text-slate-800 dark:text-slate-100">Campus Map</h5>
                  <p className="text-xs text-slate-400 mt-1">Interactive Leaflet map showing occupancy level and info.</p>
                </Link>
              </div>
            </div>

            {/* Events Column */}
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h4 className="text-sm font-extrabold text-slate-400 uppercase tracking-wider">Upcoming Events</h4>
                <Link 
                  to="/events" 
                  className="text-xs font-bold text-brand-600 dark:text-brand-400 hover:underline flex items-center gap-1"
                >
                  <span>View All</span>
                  <ArrowRight size={12} />
                </Link>
              </div>

              <div className="space-y-4">
                {events.length > 0 ? (
                  events.map((ev) => (
                    <div 
                      key={ev.id} 
                      className="p-5 rounded-3xl glass-panel border border-slate-200/50 dark:border-slate-800/40 space-y-3 relative hover:border-brand-500/10 transition-colors"
                    >
                      <div className="flex items-center justify-between">
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-indigo-50 dark:bg-dark-800 text-brand-600 dark:text-brand-400 border border-indigo-100/50 dark:border-brand-900/30">
                          {ev.category}
                        </span>
                      </div>
                      <div>
                        <h5 className="font-extrabold text-slate-800 dark:text-slate-100">{ev.title}</h5>
                        <p className="text-xs text-slate-400 dark:text-slate-500 mt-0.5 line-clamp-2">{ev.description}</p>
                      </div>
                      <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 pt-1">
                        <span className="flex items-center gap-1 font-semibold">
                          <Clock size={12} className="text-brand-500" />
                          {ev.time}
                        </span>
                        <span className="flex items-center gap-1 font-semibold">
                          <MapPin size={12} className="text-brand-500" />
                          {ev.location}
                        </span>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="glass-panel p-6 rounded-3xl text-center border border-slate-200/50 dark:border-slate-800/40 text-slate-400">
                    No upcoming events.
                  </div>
                )}
              </div>
            </div>

          </div>
        </>
      )}
    </div>
  );
};

export default Dashboard;
