import React, { useState, useEffect } from 'react';
import { 
  Calendar, 
  MapPin, 
  Clock, 
  Filter, 
  Tag, 
  Award, 
  Sparkles, 
  BookOpen, 
  Loader2 
} from 'lucide-react';
import api from '../services/api';

interface Event {
  id: number;
  title: string;
  date: string;
  time: string;
  location: string;
  category: string;
  description: string;
}

const Events: React.FC = () => {
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState('All');

  const categories = ['All', 'Technical', 'Cultural', 'Sports', 'Workshop', 'Club'];

  const fetchEvents = async () => {
    try {
      setLoading(true);
      const response = await api.get('/events');
      setEvents(response.data);
    } catch (err) {
      console.error('Error fetching campus events:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvents();
  }, []);

  const getCategoryColor = (cat: string) => {
    switch (cat) {
      case 'Technical': return 'bg-blue-50 text-blue-700 border-blue-100 dark:bg-blue-950/20 dark:text-blue-400 dark:border-blue-950/30';
      case 'Cultural': return 'bg-pink-50 text-pink-700 border-pink-100 dark:bg-pink-950/20 dark:text-pink-400 dark:border-pink-950/30';
      case 'Sports': return 'bg-emerald-50 text-emerald-700 border-emerald-100 dark:bg-emerald-950/20 dark:text-emerald-400 dark:border-emerald-950/30';
      case 'Workshop': return 'bg-amber-50 text-amber-700 border-amber-100 dark:bg-amber-950/20 dark:text-amber-400 dark:border-amber-950/30';
      case 'Club': return 'bg-purple-50 text-purple-700 border-purple-100 dark:bg-purple-950/20 dark:text-purple-400 dark:border-purple-950/30';
      default: return 'bg-slate-50 text-slate-700 border-slate-100 dark:bg-slate-800 dark:text-slate-400 dark:border-slate-800';
    }
  };

  const getTodayDateStr = () => {
    return new Date().toISOString().split('T')[0];
  };

  // Filter events
  const filteredEvents = events.filter((ev) => {
    if (selectedCategory === 'All') return true;
    return ev.category.toLowerCase() === selectedCategory.toLowerCase();
  });

  // Separate today's events
  const todayDate = getTodayDateStr();
  const todayEvents = filteredEvents.filter((e) => e.date === todayDate);
  const futureEvents = filteredEvents.filter((e) => e.date > todayDate);
  const pastEvents = filteredEvents.filter((e) => e.date < todayDate);

  const formatDateString = (dateStr: string) => {
    const d = new Date(dateStr);
    return d.toLocaleDateString(undefined, { weekday: 'long', month: 'short', day: 'numeric', year: 'numeric' });
  };

  return (
    <div className="flex-1 min-h-screen bg-slate-50/50 dark:bg-dark-950 p-6 md:p-8 space-y-8">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <p className="text-xs font-bold text-brand-600 dark:text-brand-400 uppercase tracking-wider mb-1">
            Student Life
          </p>
          <h2 className="text-3xl font-extrabold tracking-tight text-slate-800 dark:text-white">
            Campus Events
          </h2>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
            Discover workshops, club activities, seminars, sports competitions, and cultural celebrations.
          </p>
        </div>
      </div>

      {/* Category selector */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 shrink-0">
        <div className="flex items-center gap-2 mr-2 text-slate-400 dark:text-slate-500">
          <Filter size={16} />
          <span className="text-xs font-bold uppercase tracking-wider">Filters</span>
        </div>
        {categories.map((cat) => (
          <button
            key={cat}
            onClick={() => setSelectedCategory(cat)}
            className={`px-4 py-2 rounded-full text-xs font-bold border transition-all shrink-0 ${
              selectedCategory === cat
                ? 'gradient-primary text-white border-transparent shadow-md shadow-brand-500/15'
                : 'bg-white dark:bg-dark-900 border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-50'
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="h-[300px] flex items-center justify-center">
          <Loader2 className="animate-spin text-brand-500" size={32} />
        </div>
      ) : (
        <div className="space-y-10">
          
          {/* Section 1: Happening Today */}
          {todayEvents.length > 0 && (
            <div className="space-y-4">
              <h3 className="text-sm font-extrabold text-brand-600 dark:text-brand-400 uppercase tracking-wider flex items-center gap-2">
                <Sparkles size={16} className="animate-pulse" />
                <span>Happening Today</span>
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {todayEvents.map((ev) => (
                  <div 
                    key={ev.id} 
                    className="glass-panel p-6 rounded-3xl border-2 border-brand-500/30 dark:border-brand-500/20 relative flex flex-col justify-between shadow-md relative overflow-hidden group hover:border-brand-500/50 transition-colors"
                  >
                    <div className="absolute top-0 right-0 w-16 h-16 pointer-events-none">
                      <div className="absolute top-[-10px] right-[-10px] bg-brand-500 text-white text-[9px] font-black uppercase rotate-45 text-center w-20 py-1.5 shadow-sm">
                        Today
                      </div>
                    </div>

                    <div className="space-y-4">
                      <div className="flex items-center">
                        <span className={`inline-flex px-2.5 py-0.5 rounded-full text-[10px] font-extrabold border uppercase tracking-wider ${getCategoryColor(ev.category)}`}>
                          {ev.category}
                        </span>
                      </div>

                      <div>
                        <h4 className="text-lg font-black text-slate-800 dark:text-slate-100 group-hover:text-brand-600 dark:group-hover:text-brand-400 transition-colors">
                          {ev.title}
                        </h4>
                        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 font-medium leading-relaxed">
                          {ev.description}
                        </p>
                      </div>
                    </div>

                    <div className="mt-6 pt-4 border-t border-slate-100 dark:border-slate-800 grid grid-cols-2 gap-2 text-xs text-slate-500 dark:text-slate-400 font-semibold">
                      <div className="flex items-center gap-1.5">
                        <Clock size={14} className="text-brand-500" />
                        <span>{ev.time}</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <MapPin size={14} className="text-brand-500" />
                        <span className="truncate">{ev.location}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Section 2: Upcoming Events */}
          <div className="space-y-4">
            <h3 className="text-sm font-extrabold text-slate-400 uppercase tracking-wider flex items-center gap-2">
              <Calendar size={16} />
              <span>Upcoming Agenda</span>
            </h3>

            {futureEvents.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {futureEvents.map((ev) => (
                  <div 
                    key={ev.id} 
                    className="glass-panel p-6 rounded-3xl border border-slate-200/50 dark:border-slate-800/40 relative flex flex-col justify-between shadow-sm group hover:border-brand-500/15 transition-all"
                  >
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <span className={`inline-flex px-2.5 py-0.5 rounded-full text-[10px] font-extrabold border uppercase tracking-wider ${getCategoryColor(ev.category)}`}>
                          {ev.category}
                        </span>
                        <span className="text-[10px] font-bold text-slate-400">{formatDateString(ev.date)}</span>
                      </div>

                      <div>
                        <h4 className="text-lg font-black text-slate-800 dark:text-slate-100 group-hover:text-brand-600 dark:group-hover:text-brand-400 transition-colors">
                          {ev.title}
                        </h4>
                        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 font-medium leading-relaxed">
                          {ev.description}
                        </p>
                      </div>
                    </div>

                    <div className="mt-6 pt-4 border-t border-slate-100 dark:border-slate-800 grid grid-cols-2 gap-2 text-xs text-slate-500 dark:text-slate-400 font-semibold">
                      <div className="flex items-center gap-1.5">
                        <Clock size={14} className="text-brand-500" />
                        <span>{ev.time}</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <MapPin size={14} className="text-brand-500" />
                        <span className="truncate">{ev.location}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="glass-panel p-10 text-center rounded-3xl border border-slate-200/50 dark:border-slate-800/40 text-slate-400">
                No future events scheduled.
              </div>
            )}
          </div>

          {/* Section 3: Past Activities */}
          {pastEvents.length > 0 && (
            <div className="space-y-4">
              <h3 className="text-sm font-extrabold text-slate-400 uppercase tracking-wider flex items-center gap-2">
                <BookOpen size={16} />
                <span>Past Events</span>
              </h3>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 opacity-60">
                {pastEvents.map((ev) => (
                  <div 
                    key={ev.id} 
                    className="bg-white dark:bg-dark-900/60 p-6 rounded-3xl border border-slate-200/40 dark:border-slate-800/30 flex flex-col justify-between shadow-sm"
                  >
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <span className="inline-flex px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-slate-100 dark:bg-dark-800 text-slate-500 dark:text-slate-400 border border-slate-200 dark:border-slate-850 tracking-wider">
                          {ev.category}
                        </span>
                        <span className="text-[10px] text-slate-400">{formatDateString(ev.date)}</span>
                      </div>

                      <div>
                        <h4 className="text-base font-extrabold text-slate-700 dark:text-slate-350">
                          {ev.title}
                        </h4>
                        <p className="text-xs text-slate-400 mt-1">
                          {ev.description}
                        </p>
                      </div>
                    </div>

                    <div className="mt-4 pt-3 border-t border-slate-100/55 dark:border-slate-850/30 grid grid-cols-2 gap-2 text-[10px] text-slate-400 font-semibold">
                      <div className="flex items-center gap-1">
                        <Clock size={12} />
                        <span>{ev.time}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <MapPin size={12} />
                        <span className="truncate">{ev.location}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

        </div>
      )}
    </div>
  );
};

export default Events;
