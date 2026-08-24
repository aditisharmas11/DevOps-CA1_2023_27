import React, { useState, useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import { 
  Wrench, 
  Plus, 
  Clock, 
  MapPin, 
  AlertOctagon, 
  CheckCircle, 
  Loader2,
  AlertTriangle,
  FileText,
  BadgeAlert
} from 'lucide-react';
import api from '../services/api';

interface Ticket {
  id: number;
  ticket_no: string;
  issue_type: string;
  location: string;
  description: string;
  priority: 'LOW' | 'MEDIUM' | 'HIGH';
  status: 'OPEN' | 'IN PROGRESS' | 'RESOLVED';
  created_at: string;
  category: string;
}

interface MaintenanceProps {
  user: { name: string; email: string; role: string } | null;
}

const Maintenance: React.FC<MaintenanceProps> = ({ user }) => {
  const routerLocation = useLocation();
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(true);
  
  // Form states
  const [issueType, setIssueType] = useState('AC problems');
  const [roomLocation, setRoomLocation] = useState('B204');
  const [description, setDescription] = useState('');
  const [submitLoading, setSubmitLoading] = useState(false);
  const [successTicket, setSuccessTicket] = useState<string | null>(null);

  // Routing state highlight
  const [highlightedTicketNo, setHighlightedTicketNo] = useState<string | null>(null);
  
  const ticketRefs = useRef<{ [key: string]: HTMLDivElement | null }>({});

  const issueTypes = [
    'AC problems',
    'Fan problems',
    'Wi-Fi issues',
    'Projector problems',
    'Electricity issues',
    'Plumbing',
    'Furniture',
    'Cleanliness'
  ];

  const locationsList = [
    'A101', 'A102', 'A103', 'A201', 'A202', 'A203',
    'B101', 'B102', 'B201', 'B202', 'B204', 'B205', 'B206',
    'C101', 'C102', 'C103', 'C201', 'C202', 'C203', 'C204',
    'Library', 'Canteen', 'Seminar Hall', 'Sports Ground', 'Medical Center'
  ];

  const fetchTickets = async () => {
    try {
      setLoading(true);
      const response = await api.get('/maintenance');
      setTickets(response.data);
    } catch (err) {
      console.error('Error fetching maintenance tickets:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTickets();
    
    // Check if redirect passed a ticket number to highlight
    const state = routerLocation.state as { highlightTicket?: string };
    if (state && state.highlightTicket) {
      setHighlightedTicketNo(state.highlightTicket);
      
      // Clear highlight after 8 seconds
      const timer = setTimeout(() => {
        setHighlightedTicketNo(null);
      }, 8000);
      return () => clearTimeout(timer);
    }
  }, [routerLocation]);

  // Scroll to highlighted ticket
  useEffect(() => {
    if (highlightedTicketNo && ticketRefs.current[highlightedTicketNo]) {
      setTimeout(() => {
        ticketRefs.current[highlightedTicketNo!]?.scrollIntoView({
          behavior: 'smooth',
          block: 'center'
        });
      }, 500);
    }
  }, [highlightedTicketNo, tickets]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!description.trim()) return;

    setSubmitLoading(true);
    setSuccessTicket(null);

    try {
      const response = await api.post('/maintenance', {
        issue_type: issueType,
        location: roomLocation,
        description: description
      });

      const newTicket = response.data;
      setSuccessTicket(newTicket.ticket_no);
      setHighlightedTicketNo(newTicket.ticket_no);
      setDescription('');
      
      // Refresh tickets list
      fetchTickets();
    } catch (err) {
      console.error('Error reporting maintenance issue:', err);
    } finally {
      setSubmitLoading(false);
    }
  };

  const getPriorityBadge = (prio: string) => {
    switch (prio) {
      case 'HIGH':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-red-50 dark:bg-red-950/20 text-red-700 dark:text-red-400 border border-red-100 dark:border-red-900/30">
            <AlertOctagon size={10} />
            <span>High</span>
          </span>
        );
      case 'MEDIUM':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-50 dark:bg-amber-950/20 text-amber-700 dark:text-amber-400 border border-amber-100 dark:border-amber-900/30">
            <AlertTriangle size={10} />
            <span>Medium</span>
          </span>
        );
      case 'LOW':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-blue-50 dark:bg-blue-950/20 text-blue-700 dark:text-blue-400 border border-blue-100 dark:border-blue-900/30">
            <Clock size={10} />
            <span>Low</span>
          </span>
        );
      default:
        return null;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'OPEN':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wide bg-rose-50 dark:bg-rose-950/20 text-rose-600 dark:text-rose-400 border border-rose-100 dark:border-rose-900/20">
            Open
          </span>
        );
      case 'IN PROGRESS':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wide bg-amber-50 dark:bg-amber-950/20 text-amber-600 dark:text-amber-400 border border-amber-100 dark:border-amber-900/20">
            In Progress
          </span>
        );
      case 'RESOLVED':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wide bg-emerald-50 dark:bg-emerald-950/20 text-emerald-600 dark:text-emerald-400 border border-emerald-100 dark:border-emerald-900/20">
            Resolved
          </span>
        );
      default:
        return null;
    }
  };

  return (
    <div className="flex-1 min-h-screen bg-slate-50/50 dark:bg-dark-950 p-6 md:p-8 space-y-8">
      {/* Title */}
      <div>
        <p className="text-xs font-bold text-brand-600 dark:text-brand-400 uppercase tracking-wider mb-1">
          Support Center
        </p>
        <h2 className="text-3xl font-extrabold tracking-tight text-slate-800 dark:text-white">
          Smart Maintenance
        </h2>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
          Report mechanical or logistical issues. Tickets are automatically categorized and prioritized by AI.
        </p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-8 items-start">
        
        {/* Left Form Panel */}
        <div className="xl:col-span-1 space-y-6">
          <div className="glass-panel p-6 rounded-3xl border border-slate-200/50 dark:border-slate-800/40">
            <h3 className="text-lg font-bold text-slate-850 dark:text-slate-100 mb-4 flex items-center gap-2">
              <Plus size={18} className="text-brand-500" />
              <span>Report An Issue</span>
            </h3>

            {successTicket && (
              <div className="mb-5 p-4 bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-200/60 dark:border-emerald-950/30 rounded-2xl flex items-start gap-3">
                <CheckCircle className="text-emerald-500 dark:text-emerald-400 shrink-0 mt-0.5" size={18} />
                <div>
                  <p className="text-sm font-semibold text-emerald-800 dark:text-emerald-400">Ticket Submitted Successfully!</p>
                  <p className="text-xs text-emerald-600 dark:text-emerald-500 mt-0.5">
                    Logged as ticket **#{successTicket}**. AI classified priority and assigned it to the queue.
                  </p>
                </div>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Issue Type */}
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Issue Type</label>
                <select
                  value={issueType}
                  onChange={(e) => setIssueType(e.target.value)}
                  className="block w-full px-4 py-2.5 bg-white dark:bg-dark-900 border border-slate-200 dark:border-slate-800 rounded-xl text-sm text-slate-800 dark:text-slate-250 focus:outline-none focus:ring-2 focus:ring-brand-500"
                >
                  {issueTypes.map((t) => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </select>
              </div>

              {/* Location Selection */}
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Location / Room</label>
                <select
                  value={roomLocation}
                  onChange={(e) => setRoomLocation(e.target.value)}
                  className="block w-full px-4 py-2.5 bg-white dark:bg-dark-900 border border-slate-200 dark:border-slate-800 rounded-xl text-sm text-slate-800 dark:text-slate-250 focus:outline-none focus:ring-2 focus:ring-brand-500"
                >
                  {locationsList.map((loc) => (
                    <option key={loc} value={loc}>{loc}</option>
                  ))}
                </select>
              </div>

              {/* Description Text */}
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Description of Problem</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="AC in B204 is leaking water onto the projector screen..."
                  rows={4}
                  required
                  className="block w-full px-4 py-3 bg-white dark:bg-dark-900 border border-slate-200 dark:border-slate-800 rounded-xl text-sm text-slate-850 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={submitLoading || !description.trim()}
                className="w-full inline-flex items-center justify-center gap-2 px-5 py-3 rounded-2xl font-bold text-white gradient-primary shadow-md shadow-brand-500/15 hover:shadow-lg transition-all disabled:opacity-50"
              >
                {submitLoading ? (
                  <>
                    <Loader2 className="animate-spin" size={16} />
                    <span>AI Classifying issue...</span>
                  </>
                ) : (
                  <>
                    <Wrench size={16} />
                    <span>File Ticket</span>
                  </>
                )}
              </button>
            </form>
          </div>
        </div>

        {/* Right Active Tickets Queue */}
        <div className="xl:col-span-2 space-y-6">
          <h3 className="text-sm font-extrabold text-slate-400 uppercase tracking-wider">Tickets Queue</h3>

          {loading ? (
            <div className="h-[300px] flex items-center justify-center">
              <Loader2 className="animate-spin text-brand-500" size={32} />
            </div>
          ) : tickets.length > 0 ? (
            <div className="space-y-4 max-h-[600px] overflow-y-auto pr-1">
              {tickets.map((ticket) => {
                const isHighlighted = highlightedTicketNo === ticket.ticket_no;
                
                return (
                  <div
                    key={ticket.id}
                    ref={(el) => { ticketRefs.current[ticket.ticket_no] = el; }}
                    className={`p-5 rounded-3xl glass-panel border shadow-sm transition-all duration-500 ${
                      isHighlighted 
                        ? 'border-pink-500 dark:border-pink-500 ring-4 ring-pink-500/10 scale-[1.01] bg-pink-50/10 dark:bg-pink-950/10' 
                        : 'border-slate-200/50 dark:border-slate-800/40 hover:border-brand-500/15'
                    }`}
                  >
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100 dark:border-slate-800">
                      <div className="flex items-center gap-2.5">
                        <span className="font-black text-slate-800 dark:text-slate-100">
                          #{ticket.ticket_no}
                        </span>
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-slate-100 dark:bg-dark-800 text-slate-650 dark:text-slate-400">
                          {ticket.category}
                        </span>
                      </div>
                      
                      <div className="flex items-center gap-2">
                        {getPriorityBadge(ticket.priority)}
                        {getStatusBadge(ticket.status)}
                      </div>
                    </div>

                    <div className="space-y-3 pt-3">
                      <div>
                        <h4 className="text-sm font-bold text-slate-700 dark:text-slate-250">
                          {ticket.issue_type}
                        </h4>
                        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 font-medium leading-relaxed">
                          {ticket.description}
                        </p>
                      </div>

                      <div className="flex flex-wrap items-center justify-between gap-3 text-[10px] text-slate-400 font-bold uppercase tracking-wider pt-1.5">
                        <div className="flex items-center gap-1">
                          <MapPin size={12} className="text-brand-500" />
                          <span>Location: {ticket.location}</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <FileText size={12} className="text-brand-500" />
                          <span>Filed: {ticket.created_at}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="glass-panel p-12 text-center rounded-3xl border border-slate-200/50 dark:border-slate-800/40 text-slate-400">
              No active maintenance tickets logged in the system.
            </div>
          )}
        </div>

      </div>
    </div>
  );
};

export default Maintenance;
