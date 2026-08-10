import React, { useState, useEffect } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  AreaChart, Area
} from 'recharts';
import { 
  Users, 
  School, 
  Activity, 
  Wrench, 
  Calendar, 
  Loader2,
  CheckCircle,
  Play,
  RotateCw,
  AlertTriangle,
  MapPin,
  Clock,
  Cpu,
  RefreshCw,
  TrendingUp
} from 'lucide-react';
import api from '../services/api';

interface AdminDashboardProps {
  user: { name: string; email: string; role: string } | null;
  activeTab: 'analytics' | 'occupancy' | 'sensors';
}

const AdminDashboard: React.FC<AdminDashboardProps> = ({ user, activeTab }) => {
  const [stats, setStats] = useState({
    totalStudents: 4821,
    availableClassrooms: 18,
    occupancy: 67,
    openIssues: 12,
    todayEvents: 5
  });

  const [classrooms, setClassrooms] = useState<any[]>([]);
  const [occupancies, setOccupancies] = useState<any[]>([]);
  const [tickets, setTickets] = useState<any[]>([]);
  const [sensors, setSensors] = useState<any[]>([]);
  
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<number | null>(null);
  const [simulating, setSimulating] = useState(false);

  const fetchData = async () => {
    try {
      setLoading(true);
      const roomsRes = await api.get('/classrooms');
      setClassrooms(roomsRes.data);
      
      const occRes = await api.get('/occupancy');
      setOccupancies(occRes.data);
      
      const maintRes = await api.get('/maintenance');
      setTickets(maintRes.data);
      
      const eventsRes = await api.get('/events');
      const todayStr = new Date().toISOString().split('T')[0];
      const todayEvs = eventsRes.data.filter((e: any) => e.date === todayStr).length;

      const sensorsRes = await api.get('/sensors');
      setSensors(sensorsRes.data);

      const available = roomsRes.data.filter((r: any) => r.status === 'AVAILABLE').length;
      const avgOcc = occRes.data.length > 0
        ? Math.round(occRes.data.reduce((acc: number, item: any) => acc + item.occupancy_pct, 0) / occRes.data.length)
        : 67;
      const open = maintRes.data.filter((t: any) => t.status !== 'RESOLVED').length;

      setStats({
        totalStudents: 4821,
        availableClassrooms: available,
        occupancy: avgOcc,
        openIssues: open,
        todayEvents: todayEvs
      });
    } catch (err) {
      console.error('Error fetching admin data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [activeTab]);

  // Handle ticket status change
  const handleUpdateStatus = async (ticketId: number, currentStatus: string) => {
    let nextStatus = 'IN PROGRESS';
    if (currentStatus === 'IN PROGRESS') {
      nextStatus = 'RESOLVED';
    } else if (currentStatus === 'RESOLVED') {
      nextStatus = 'OPEN';
    }

    try {
      setActionLoading(ticketId);
      await api.put(`/maintenance/${ticketId}`, { status: nextStatus });
      // Refresh local list
      fetchData();
    } catch (err) {
      console.error('Error updating ticket status:', err);
    } finally {
      setActionLoading(null);
    }
  };

  // Simulate occupancy updates
  const handleSimulateOccupancy = async () => {
    try {
      setSimulating(true);
      const res = await api.post('/occupancy/simulate');
      
      // Update stats and details
      fetchData();
    } catch (err) {
      console.error('Error simulating occupancy:', err);
    } finally {
      setSimulating(false);
    }
  };

  // Simulate sensor updates
  const handleSimulateSensors = async () => {
    try {
      setSimulating(true);
      const res = await api.post('/sensors/simulate');
      setSensors(res.data.sensors);
    } catch (err) {
      console.error('Error simulating sensors:', err);
    } finally {
      setSimulating(false);
    }
  };

  // Prepare chart data: Top classrooms by occupancy for visualization
  const getClassroomChartData = () => {
    // Take a mix of classrooms for visual display
    const sampleRooms = classrooms.filter((r: any) => ['B204', 'B205', 'B206', 'A101', 'A102', 'C101'].includes(r.name));
    return sampleRooms.map((r: any) => ({
      name: r.name,
      occupancy: r.occupancy_pct,
      capacity: r.capacity
    }));
  };

  const getOccupancyChartData = () => {
    return occupancies.map((o: any) => ({
      name: o.building_name,
      occupancy: o.occupancy_pct
    }));
  };

  const getPriorityColor = (prio: string) => {
    switch (prio) {
      case 'HIGH': return 'text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950/20 border-red-100 dark:border-red-900/30';
      case 'MEDIUM': return 'text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/20 border-amber-100 dark:border-amber-900/30';
      default: return 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-950/20 border-blue-100 dark:border-blue-900/30';
    }
  };

  return (
    <div className="flex-1 min-h-screen bg-slate-50/50 dark:bg-dark-950 p-6 md:p-8 space-y-8">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <p className="text-xs font-bold text-brand-600 dark:text-brand-400 uppercase tracking-wider mb-1">
            Administration Portal
          </p>
          <h2 className="text-3xl font-extrabold tracking-tight text-slate-800 dark:text-white">
            {activeTab === 'analytics' && 'Analytics Overview'}
            {activeTab === 'occupancy' && 'Live Occupancy Hub'}
            {activeTab === 'sensors' && 'IoT Device Fleet'}
          </h2>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
            Monitor and coordinate campus operations, simulate real-time sensors, and resolve student tickets.
          </p>
        </div>
      </div>

      {loading ? (
        <div className="h-[400px] flex items-center justify-center">
          <Loader2 className="animate-spin text-brand-500" size={32} />
        </div>
      ) : (
        <>
          {/* Admin Stats Grid */}
          <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
            <div className="glass-panel p-4 rounded-2xl shadow-sm border border-slate-200/50 dark:border-slate-800/40">
              <span className="text-slate-400 dark:text-slate-500 text-[10px] font-bold uppercase tracking-wider">Total Students</span>
              <h3 className="text-2xl font-black text-slate-800 dark:text-slate-100 mt-1">{stats.totalStudents.toLocaleString()}</h3>
            </div>
            <div className="glass-panel p-4 rounded-2xl shadow-sm border border-slate-200/50 dark:border-slate-800/40">
              <span className="text-slate-400 dark:text-slate-500 text-[10px] font-bold uppercase tracking-wider">Available Rooms</span>
              <h3 className="text-2xl font-black text-slate-800 dark:text-slate-100 mt-1">{stats.availableClassrooms}</h3>
            </div>
            <div className="glass-panel p-4 rounded-2xl shadow-sm border border-slate-200/50 dark:border-slate-800/40">
              <span className="text-slate-400 dark:text-slate-500 text-[10px] font-bold uppercase tracking-wider">Campus Occupancy</span>
              <h3 className="text-2xl font-black text-slate-800 dark:text-slate-100 mt-1">{stats.occupancy}%</h3>
            </div>
            <div className="glass-panel p-4 rounded-2xl shadow-sm border border-slate-200/50 dark:border-slate-800/40">
              <span className="text-slate-400 dark:text-slate-500 text-[10px] font-bold uppercase tracking-wider">Open Maintenance</span>
              <h3 className="text-2xl font-black text-slate-800 dark:text-slate-100 mt-1 text-red-650 dark:text-red-400">{stats.openIssues}</h3>
            </div>
            <div className="glass-panel p-4 rounded-2xl shadow-sm border border-slate-200/50 dark:border-slate-800/40 col-span-2 lg:col-span-1">
              <span className="text-slate-400 dark:text-slate-500 text-[10px] font-bold uppercase tracking-wider">Today's Events</span>
              <h3 className="text-2xl font-black text-slate-800 dark:text-slate-100 mt-1">{stats.todayEvents}</h3>
            </div>
          </div>

          {/* Tab 1: Analytics / Dashboard Charts */}
          {activeTab === 'analytics' && (
            <div className="space-y-8">
              
              {/* Charts grid */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Classroom utilization bar chart */}
                <div className="glass-panel p-6 rounded-3xl border border-slate-200/50 dark:border-slate-800/40 shadow-sm space-y-4">
                  <div className="flex items-center justify-between">
                    <h4 className="font-extrabold text-slate-850 dark:text-slate-100 text-sm uppercase tracking-wider">
                      Classroom Utilization (%)
                    </h4>
                    <span className="inline-flex items-center gap-1 text-xs text-brand-650 dark:text-brand-400 font-bold">
                      <TrendingUp size={14} /> Sampled Rooms
                    </span>
                  </div>
                  <div className="h-64 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={getClassroomChartData()} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                        <XAxis dataKey="name" stroke="#94a3b8" fontSize={11} tickLine={false} />
                        <YAxis stroke="#94a3b8" fontSize={11} domain={[0, 100]} tickLine={false} />
                        <Tooltip 
                          contentStyle={{ background: 'rgba(15,23,42,0.95)', border: 'none', borderRadius: '12px', color: '#fff', fontSize: '12px' }}
                          cursor={{ fill: 'rgba(99,102,241,0.05)' }}
                        />
                        <Bar dataKey="occupancy" fill="#6366f1" radius={[8, 8, 0, 0]} barSize={28} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* Building occupancies area chart */}
                <div className="glass-panel p-6 rounded-3xl border border-slate-200/50 dark:border-slate-800/40 shadow-sm space-y-4">
                  <div className="flex items-center justify-between">
                    <h4 className="font-extrabold text-slate-850 dark:text-slate-100 text-sm uppercase tracking-wider">
                      Campus Building Occupancy (%)
                    </h4>
                    <span className="inline-flex items-center gap-1 text-xs text-emerald-650 dark:text-emerald-400 font-bold">
                      <Activity size={14} /> Fictional IoT Sensors
                    </span>
                  </div>
                  <div className="h-64 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <AreaChart data={getOccupancyChartData()} margin={{ top: 10, right: 10, left: -25, bottom: 0 }}>
                        <defs>
                          <linearGradient id="colorOcc" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                            <stop offset="95%" stopColor="#10b981" stopOpacity={0.0}/>
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                        <XAxis dataKey="name" stroke="#94a3b8" fontSize={11} tickLine={false} />
                        <YAxis stroke="#94a3b8" fontSize={11} domain={[0, 100]} tickLine={false} />
                        <Tooltip 
                          contentStyle={{ background: 'rgba(15,23,42,0.95)', border: 'none', borderRadius: '12px', color: '#fff', fontSize: '12px' }}
                        />
                        <Area type="monotone" dataKey="occupancy" stroke="#10b981" fillOpacity={1} fill="url(#colorOcc)" strokeWidth={2.5} />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>

              {/* Maintenance resolution queue */}
              <div className="glass-panel p-6 rounded-3xl border border-slate-200/50 dark:border-slate-800/40 shadow-sm space-y-5">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-extrabold text-slate-850 dark:text-slate-100 text-sm uppercase tracking-wider">
                      Maintenance Ticket Desk
                    </h4>
                    <p className="text-xs text-slate-400 font-semibold mt-0.5">Toggle status triggers to route tickets: Open → In Progress → Resolved</p>
                  </div>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs font-semibold text-slate-500 dark:text-slate-400">
                    <thead className="text-[10px] text-slate-400 uppercase border-b border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-dark-900/30">
                      <tr>
                        <th className="py-3 px-4 rounded-l-xl">Ticket ID</th>
                        <th className="py-3 px-4">Category</th>
                        <th className="py-3 px-4">Problem</th>
                        <th className="py-3 px-4">Location</th>
                        <th className="py-3 px-4">Priority</th>
                        <th className="py-3 px-4">Status</th>
                        <th className="py-3 px-4 rounded-r-xl text-center">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                      {tickets.slice(0, 8).map((t) => (
                        <tr key={t.id} className="hover:bg-slate-50/30 dark:hover:bg-dark-900/10">
                          <td className="py-3.5 px-4 font-black text-slate-800 dark:text-slate-200">#{t.ticket_no}</td>
                          <td className="py-3.5 px-4">{t.category}</td>
                          <td className="py-3.5 px-4 max-w-[200px] truncate text-slate-700 dark:text-slate-300" title={t.description}>
                            {t.issue_type}
                          </td>
                          <td className="py-3.5 px-4">{t.location}</td>
                          <td className="py-3.5 px-4">
                            <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase border ${getPriorityColor(t.priority)}`}>
                              {t.priority}
                            </span>
                          </td>
                          <td className="py-3.5 px-4">
                            <span className={`px-2 py-0.5 rounded text-[10px] font-black uppercase ${
                              t.status === 'RESOLVED' ? 'bg-emerald-50 text-emerald-600 dark:bg-emerald-950/10' : t.status === 'IN PROGRESS' ? 'bg-amber-50 text-amber-600 dark:bg-amber-950/10' : 'bg-red-50 text-red-600 dark:bg-red-950/10'
                            }`}>
                              {t.status}
                            </span>
                          </td>
                          <td className="py-3.5 px-4 text-center">
                            <button
                              onClick={() => handleUpdateStatus(t.id, t.status)}
                              disabled={actionLoading === t.id}
                              className="px-3 py-1.5 gradient-primary hover:opacity-90 text-white font-bold rounded-lg transition-colors flex items-center gap-1 mx-auto disabled:opacity-50"
                            >
                              {actionLoading === t.id ? (
                                <RotateCw className="animate-spin" size={12} />
                              ) : (
                                <>
                                  <Play size={10} fill="white" />
                                  <span>Advance</span>
                                </>
                              )}
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

            </div>
          )}

          {/* Tab 2: Occupancy hub */}
          {activeTab === 'occupancy' && (
            <div className="glass-panel p-6 rounded-3xl border border-slate-200/50 dark:border-slate-800/40 shadow-sm space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <h4 className="font-extrabold text-slate-850 dark:text-slate-100 text-base uppercase tracking-wider">
                    Building Density Metrics
                  </h4>
                  <p className="text-xs text-slate-400 font-semibold mt-0.5">Click the simulator button to update telemetry logs.</p>
                </div>
                
                <button
                  onClick={handleSimulateOccupancy}
                  disabled={simulating}
                  className="px-4 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-xl shadow-md shadow-emerald-500/10 flex items-center gap-2 self-start transition-colors disabled:opacity-50"
                >
                  {simulating ? (
                    <RefreshCw className="animate-spin" size={14} />
                  ) : (
                    <RotateCw size={14} />
                  )}
                  <span>Simulate Occupancy Update</span>
                </button>
              </div>

              <div className="space-y-6 max-w-2xl">
                {occupancies.map((o) => (
                  <div key={o.id} className="space-y-2">
                    <div className="flex justify-between items-center text-sm font-semibold">
                      <span className="text-slate-800 dark:text-slate-200">{o.building_name}</span>
                      <span className="font-bold text-slate-500">{o.occupancy_pct}% capacity filled</span>
                    </div>
                    <div className="relative w-full h-4 bg-slate-100 dark:bg-dark-800 rounded-full overflow-hidden border border-slate-200/20 dark:border-dark-700/30">
                      <div 
                        className={`h-full rounded-full transition-all duration-1000 ${
                          o.occupancy_pct > 80 
                            ? 'bg-gradient-to-r from-red-500 to-rose-600' 
                            : o.occupancy_pct > 50 
                            ? 'bg-gradient-to-r from-amber-500 to-orange-500' 
                            : 'bg-gradient-to-r from-emerald-500 to-teal-500'
                        }`} 
                        style={{ width: `${o.occupancy_pct}%` }}
                      ></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Tab 3: Sensors simulation */}
          {activeTab === 'sensors' && (
            <div className="glass-panel p-6 rounded-3xl border border-slate-200/50 dark:border-slate-800/40 shadow-sm space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <h4 className="font-extrabold text-slate-850 dark:text-slate-100 text-base uppercase tracking-wider">
                    Virtual Telemetry Hub
                  </h4>
                  <p className="text-xs text-slate-400 font-semibold mt-0.5">Control fictional hardware signals linked to classrooms and energy logs.</p>
                </div>
                
                <button
                  onClick={handleSimulateSensors}
                  disabled={simulating}
                  className="px-4 py-2.5 bg-brand-600 hover:bg-brand-500 text-white font-bold text-xs rounded-xl shadow-md shadow-brand-500/10 flex items-center gap-2 self-start transition-colors disabled:opacity-50"
                >
                  {simulating ? (
                    <RefreshCw className="animate-spin" size={14} />
                  ) : (
                    <Cpu size={14} />
                  )}
                  <span>Simulate Sensor Update</span>
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                {sensors.map((sensor) => (
                  <div 
                    key={sensor.id}
                    className="p-5 bg-white dark:bg-dark-900 border border-slate-200/50 dark:border-slate-800/40 rounded-3xl flex flex-col justify-between shadow-sm hover:border-brand-500/15 transition-all"
                  >
                    <div className="space-y-4">
                      {/* Name and Status */}
                      <div className="flex items-start justify-between">
                        <div>
                          <h5 className="font-extrabold text-slate-800 dark:text-slate-100 text-sm leading-tight">
                            {sensor.name}
                          </h5>
                          <span className="text-[9px] text-slate-400 font-bold uppercase tracking-wider mt-0.5 block">
                            Type: {sensor.type}
                          </span>
                        </div>
                        <span className={`inline-flex px-2 py-0.5 rounded-full text-[9px] font-bold uppercase border tracking-wider ${
                          sensor.status === 'ONLINE' 
                            ? 'bg-emerald-50 text-emerald-600 border-emerald-100 dark:bg-emerald-950/20' 
                            : 'bg-red-50 text-red-650 border-red-150 dark:bg-red-950/20'
                        }`}>
                          {sensor.status}
                        </span>
                      </div>

                      {/* Value and Telemetry */}
                      <div className="p-4 bg-slate-50 dark:bg-dark-950/50 rounded-2xl border border-slate-200/20 dark:border-dark-800/20">
                        <label className="text-[9px] font-bold text-slate-400 uppercase tracking-wider block">Live Stream</label>
                        <span className="text-2xl font-black text-brand-650 dark:text-brand-400 mt-1 block">
                          {sensor.value}
                        </span>
                      </div>
                    </div>

                    <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                      <span>Status Code: {sensor.status === 'ONLINE' ? '200 OK' : '503 ERR'}</span>
                      <span>Sync: {sensor.last_updated}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

        </>
      )}
    </div>
  );
};

export default AdminDashboard;
