import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Search, 
  Filter, 
  Tv, 
  Wind, 
  Users, 
  CheckCircle, 
  XCircle, 
  AlertTriangle,
  Award,
  Loader2,
  MapPin,
  Sparkles
} from 'lucide-react';
import api from '../services/api';

const Classrooms: React.FC = () => {
  const [rooms, setRooms] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Filter States
  const [selectedBuilding, setSelectedBuilding] = useState('All');
  const [minCapacity, setMinCapacity] = useState<number>(0);
  const [availableOnly, setAvailableOnly] = useState(false);
  const [projectorRequired, setProjectorRequired] = useState(false);

  // Recommendation engine state
  const [reqCapacity, setReqCapacity] = useState<number>(40);
  const [reqProjector, setReqProjector] = useState(true);
  const [reqAC, setReqAC] = useState(false);
  const [recommendedRoom, setRecommendedRoom] = useState<any | null>(null);

  const navigate = useNavigate();

  const buildings = ['All', 'Block A', 'Block B', 'Block C'];

  const fetchClassrooms = async () => {
    try {
      setLoading(true);
      const params: any = {};
      if (selectedBuilding !== 'All') params.building = selectedBuilding;
      if (minCapacity > 0) params.capacity = minCapacity;
      if (availableOnly) params.available = 'true';
      if (projectorRequired) params.projector = '1';

      const response = await api.get('/classrooms', { params });
      setRooms(response.data);
    } catch (err) {
      console.error('Error fetching classrooms:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchClassrooms();
  }, [selectedBuilding, minCapacity, availableOnly, projectorRequired]);

  // Recommendation System
  const findRecommendation = () => {
    if (rooms.length === 0) {
      setRecommendedRoom(null);
      return;
    }

    // Filter local list for AVAILABLE, capacity >= requested, matching projector & AC
    let candidates = rooms.filter(r => r.status === 'AVAILABLE' && r.capacity >= reqCapacity);
    
    if (reqProjector) {
      candidates = candidates.filter(r => r.projector === 1);
    }
    if (reqAC) {
      candidates = candidates.filter(r => r.ac === 1);
    }

    // Sort candidates by capacity (we want the smallest capacity room that fits, to save space)
    // and then by occupancy pct
    candidates.sort((a, b) => {
      if (a.capacity !== b.capacity) {
        return a.capacity - b.capacity;
      }
      return a.occupancy_pct - b.occupancy_pct;
    });

    if (candidates.length > 0) {
      setRecommendedRoom(candidates[0]);
    } else {
      // Relax AC constraints first, then projector
      let relaxed = rooms.filter(r => r.status === 'AVAILABLE' && r.capacity >= reqCapacity);
      if (reqProjector) {
        relaxed = relaxed.filter(r => r.projector === 1);
      }
      
      relaxed.sort((a, b) => a.capacity - b.capacity);
      if (relaxed.length > 0) {
        setRecommendedRoom({ ...relaxed[0], relaxed: true });
      } else {
        setRecommendedRoom(null);
      }
    }
  };

  // Run recommendation whenever parameters change
  useEffect(() => {
    findRecommendation();
  }, [reqCapacity, reqProjector, reqAC, rooms]);

  // Render a visual utilization bar (e.g., ████░░░░░░ 40%)
  const renderUtilizationBar = (pct: number) => {
    const totalBlocks = 10;
    const filledBlocks = Math.round(pct / 10);
    const emptyBlocks = totalBlocks - filledBlocks;
    
    let blocksStr = '█'.repeat(filledBlocks) + '░'.repeat(emptyBlocks);
    
    return (
      <div className="font-mono text-xs text-brand-600 dark:text-brand-400 font-extrabold flex items-center gap-2">
        <span className="tracking-[0.1em]">{blocksStr}</span>
        <span>{pct}%</span>
      </div>
    );
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'AVAILABLE':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-50 dark:bg-emerald-950/20 text-emerald-700 dark:text-emerald-400 border border-emerald-100 dark:border-emerald-900/30">
            <CheckCircle size={12} />
            <span>Available</span>
          </span>
        );
      case 'OCCUPIED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-50 dark:bg-amber-950/20 text-amber-700 dark:text-amber-400 border border-amber-100 dark:border-amber-900/30">
            <Users size={12} />
            <span>Occupied</span>
          </span>
        );
      case 'FULL':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-red-50 dark:bg-red-950/20 text-red-700 dark:text-red-400 border border-red-100 dark:border-red-900/30">
            <XCircle size={12} />
            <span>Full</span>
          </span>
        );
      case 'MAINTENANCE':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold bg-slate-100 dark:bg-dark-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-800/40">
            <AlertTriangle size={12} />
            <span>Maintenance</span>
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
          Campus Resources
        </p>
        <h2 className="text-3xl font-extrabold tracking-tight text-slate-800 dark:text-white">
          Smart Classrooms
        </h2>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
          View classroom statuses, capacities, environmental settings, and occupancy utilization metrics.
        </p>
      </div>

      {/* Recommended Room Hero Panel */}
      <div className="p-6 rounded-3xl bg-gradient-to-r from-brand-600 via-indigo-600 to-indigo-700 text-white shadow-xl shadow-brand-500/10 flex flex-col md:flex-row md:items-center justify-between gap-6 relative overflow-hidden">
        <div className="absolute top-[-50%] right-[-10%] w-[300px] h-[300px] rounded-full bg-white/5 blur-[50px] pointer-events-none"></div>
        <div className="space-y-4 max-w-xl">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-white/10 rounded-full text-xs font-bold tracking-wide uppercase">
            <Sparkles size={14} className="animate-spin-slow" />
            <span>Room Recommender</span>
          </div>
          <h3 className="text-2xl font-black tracking-tight">Need a workspace right now?</h3>
          <p className="text-sm text-indigo-100 leading-relaxed font-medium">
            Select your capacity and equipment needs. Our local recommendation system will find you the most efficient available classroom.
          </p>
          
          {/* Quick inputs inside hero banner */}
          <div className="flex flex-wrap items-center gap-4 pt-1">
            {/* Capacity Input */}
            <div className="flex flex-col">
              <label className="text-[10px] font-bold text-indigo-200 uppercase tracking-wider mb-1">Capacity Needed</label>
              <input
                type="number"
                value={reqCapacity}
                onChange={(e) => setReqCapacity(Number(e.target.value))}
                className="px-3 py-1.5 bg-white/15 border border-white/20 rounded-xl text-xs font-semibold text-white focus:outline-none focus:ring-2 focus:ring-white w-24"
              />
            </div>
            
            {/* Projector Checkbox */}
            <label className="flex items-center gap-2 mt-4 cursor-pointer">
              <input
                type="checkbox"
                checked={reqProjector}
                onChange={(e) => setReqProjector(e.target.checked)}
                className="w-4 h-4 rounded-md bg-white/10 border-white/20 text-brand-600 focus:ring-0 focus:ring-offset-0"
              />
              <span className="text-xs font-semibold text-indigo-100">Projector</span>
            </label>

            {/* AC Checkbox */}
            <label className="flex items-center gap-2 mt-4 cursor-pointer">
              <input
                type="checkbox"
                checked={reqAC}
                onChange={(e) => setReqAC(e.target.checked)}
                className="w-4 h-4 rounded-md bg-white/10 border-white/20 text-brand-600 focus:ring-0 focus:ring-offset-0"
              />
              <span className="text-xs font-semibold text-indigo-100">Working AC</span>
            </label>
          </div>
        </div>

        {/* Recommended Result Box */}
        <div className="p-5 bg-white/10 rounded-2xl border border-white/15 min-w-[240px] flex flex-col justify-between shrink-0">
          {recommendedRoom ? (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-extrabold uppercase bg-white text-brand-700 px-2 py-0.5 rounded-md tracking-wider">
                  {recommendedRoom.relaxed ? 'Alternative Match' : 'Best Match'}
                </span>
                <span className="text-xs font-semibold">{recommendedRoom.building}</span>
              </div>
              <div>
                <h4 className="text-3xl font-black">{recommendedRoom.name}</h4>
                <p className="text-xs text-indigo-100 mt-1 font-medium">Fits up to {recommendedRoom.capacity} students</p>
              </div>
              <div className="flex gap-2 text-xs">
                {recommendedRoom.projector === 1 && <span className="inline-flex items-center gap-0.5">✓ TV/Proj</span>}
                {recommendedRoom.ac === 1 && <span className="inline-flex items-center gap-0.5">✓ AC</span>}
              </div>
              <button
                onClick={() => navigate('/map', { state: { highlight: recommendedRoom.building, room: recommendedRoom.name } })}
                className="w-full text-center py-2 bg-white hover:bg-slate-100 text-brand-700 font-bold text-xs rounded-xl shadow-md transition-colors"
              >
                View on Map
              </button>
            </div>
          ) : (
            <div className="h-full flex items-center justify-center text-center p-4 text-xs font-semibold text-indigo-100">
              No matching room available.
            </div>
          )}
        </div>
      </div>

      {/* Main Classroom Query Layout */}
      <div className="grid grid-cols-1 xl:grid-cols-4 gap-6 items-start">
        
        {/* Sidebar Filters */}
        <div className="xl:col-span-1 glass-panel p-6 rounded-3xl border border-slate-200/50 dark:border-slate-800/40 space-y-6">
          <div className="flex items-center gap-2 text-slate-800 dark:text-slate-100">
            <Filter size={18} className="text-brand-500" />
            <h4 className="font-bold">Filters</h4>
          </div>

          {/* Building Filter */}
          <div className="space-y-2">
            <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Building</label>
            <div className="flex flex-wrap gap-2">
              {buildings.map((b) => (
                <button
                  key={b}
                  onClick={() => setSelectedBuilding(b)}
                  className={`px-3 py-1.5 rounded-xl text-xs font-semibold border transition-all ${
                    selectedBuilding === b
                      ? 'gradient-primary text-white border-transparent'
                      : 'bg-white dark:bg-dark-900 border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-50'
                  }`}
                >
                  {b}
                </button>
              ))}
            </div>
          </div>

          {/* Capacity Slider */}
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Minimum Capacity</label>
              <span className="text-xs font-bold text-brand-600 dark:text-brand-400">{minCapacity} seats</span>
            </div>
            <input
              type="range"
              min="0"
              max="150"
              step="10"
              value={minCapacity}
              onChange={(e) => setMinCapacity(Number(e.target.value))}
              className="w-full h-1.5 bg-slate-200 dark:bg-dark-800 rounded-lg appearance-none cursor-pointer accent-brand-500"
            />
          </div>

          {/* Toggle Switches */}
          <div className="space-y-4 pt-2">
            {/* Available Toggle */}
            <label className="flex items-center justify-between cursor-pointer">
              <span className="text-sm font-semibold text-slate-600 dark:text-slate-300">Available Rooms Only</span>
              <input
                type="checkbox"
                checked={availableOnly}
                onChange={(e) => setAvailableOnly(e.target.checked)}
                className="w-9 h-5 bg-slate-200 dark:bg-dark-800 rounded-full appearance-none checked:bg-brand-500 relative cursor-pointer outline-none transition-colors duration-200 before:content-[''] before:absolute before:w-4 before:h-4 before:bg-white before:rounded-full before:top-[2px] before:left-[2px] checked:before:translate-x-4 before:transition-transform"
              />
            </label>

            {/* Projector Toggle */}
            <label className="flex items-center justify-between cursor-pointer">
              <span className="text-sm font-semibold text-slate-600 dark:text-slate-300">Has Projector / TV</span>
              <input
                type="checkbox"
                checked={projectorRequired}
                onChange={(e) => setProjectorRequired(e.target.checked)}
                className="w-9 h-5 bg-slate-200 dark:bg-dark-800 rounded-full appearance-none checked:bg-brand-500 relative cursor-pointer outline-none transition-colors duration-200 before:content-[''] before:absolute before:w-4 before:h-4 before:bg-white before:rounded-full before:top-[2px] before:left-[2px] checked:before:translate-x-4 before:transition-transform"
              />
            </label>
          </div>
        </div>

        {/* Classrooms Grid (Main area) */}
        <div className="xl:col-span-3 space-y-6">
          {loading ? (
            <div className="h-[300px] flex items-center justify-center">
              <Loader2 className="animate-spin text-brand-500" size={32} />
            </div>
          ) : rooms.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {rooms.map((room) => (
                <div 
                  key={room.id}
                  className="glass-panel p-5 rounded-3xl border border-slate-200/50 dark:border-slate-800/40 relative flex flex-col justify-between hover:border-brand-500/20 shadow-sm transition-all"
                >
                  <div className="space-y-4">
                    {/* Header */}
                    <div className="flex items-start justify-between">
                      <div>
                        <h4 className="text-xl font-extrabold text-slate-800 dark:text-slate-100">{room.name}</h4>
                        <p className="text-[10px] text-slate-400 font-bold uppercase tracking-wider mt-0.5">{room.building}</p>
                      </div>
                      {getStatusBadge(room.status)}
                    </div>

                    {/* Stats List */}
                    <div className="space-y-2 text-xs font-semibold text-slate-500 dark:text-slate-400">
                      <div className="flex justify-between items-center">
                        <span className="flex items-center gap-1"><Users size={14} className="text-brand-500" /> Capacity</span>
                        <span className="text-slate-800 dark:text-slate-200">{room.capacity} students</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="flex items-center gap-1"><Tv size={14} className="text-brand-500" /> Projector</span>
                        <span className={`px-2 py-0.5 rounded text-[10px] ${room.projector === 1 ? 'bg-emerald-50 dark:bg-emerald-950/20 text-emerald-600 dark:text-emerald-400' : 'bg-slate-100 dark:bg-dark-800 text-slate-500 dark:text-slate-400'}`}>
                          {room.projector === 1 ? '✓ Available' : '✗ None'}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="flex items-center gap-1"><Wind size={14} className="text-brand-500" /> Air Conditioning</span>
                        <span className={`px-2 py-0.5 rounded text-[10px] ${room.ac === 1 ? 'bg-emerald-50 dark:bg-emerald-950/20 text-emerald-600 dark:text-emerald-400' : 'bg-slate-100 dark:bg-dark-800 text-slate-500 dark:text-slate-400'}`}>
                          {room.ac === 1 ? '✓ Working' : '✗ Broken/None'}
                        </span>
                      </div>
                    </div>

                    {/* Utilization Index */}
                    <div className="space-y-1.5 pt-2 border-t border-slate-100 dark:border-slate-800">
                      <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Live Utilization</label>
                      {renderUtilizationBar(room.occupancy_pct)}
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="mt-5 pt-3 border-t border-slate-100 dark:border-slate-800 flex gap-2">
                    <button
                      onClick={() => navigate('/map', { state: { highlight: room.building, room: room.name } })}
                      className="flex-1 text-center py-2 bg-slate-50 hover:bg-slate-100 dark:bg-dark-900 dark:hover:bg-dark-800 text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-800 font-bold text-xs rounded-xl shadow-sm transition-all"
                    >
                      View on Map
                    </button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="glass-panel p-12 text-center rounded-3xl border border-slate-200/50 dark:border-slate-800/40 text-slate-400">
              No classrooms match your filter selections.
            </div>
          )}
        </div>

      </div>
    </div>
  );
};

export default Classrooms;
