import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import { 
  MapPin, 
  Clock, 
  Activity, 
  BookOpen, 
  Navigation, 
  Building,
  GraduationCap,
  Waves
} from 'lucide-react';
import api from '../services/api';
import 'leaflet/dist/leaflet.css';

// Fix Leaflet missing icon bug by creating modern custom SVG pins
const createCustomIcon = (color: string) => {
  return L.divIcon({
    className: 'custom-leaflet-icon',
    html: `
      <div class="flex items-center justify-center w-8 h-8 rounded-full shadow-lg border-2 border-white transition-all transform hover:scale-110" style="background: ${color};">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"></path>
          <circle cx="12" cy="10" r="3"></circle>
        </svg>
      </div>
    `,
    iconSize: [32, 32],
    iconAnchor: [16, 32],
    popupAnchor: [0, -32]
  });
};

const highlightedIcon = L.divIcon({
  className: 'custom-leaflet-icon-highlighted',
  html: `
    <div class="flex items-center justify-center w-10 h-10 rounded-full shadow-xl border-4 border-white animate-bounce" style="background: linear-gradient(135deg, #ec4899 0%, #d946ef 100%);">
      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <polygon points="12 2 22 8.5 22 15.5 12 22 2 15.5 2 8.5 12 2"></polygon>
        <line x1="12" y1="22" x2="12" y2="15.5"></line>
        <polyline points="22 8.5 12 15.5 2 8.5"></polyline>
        <polyline points="2 15.5 12 8.5 22 15.5"></polyline>
        <line x1="12" y1="2" x2="12" y2="8.5"></line>
      </svg>
    </div>
  `,
  iconSize: [40, 40],
  iconAnchor: [20, 40],
  popupAnchor: [0, -40]
});

// Map Controller to programmatically pan/zoom when location state changes
const MapController: React.FC<{ coords: [number, number]; highlight: string | null }> = ({ coords, highlight }) => {
  const map = useMap();
  
  useEffect(() => {
    if (coords && highlight) {
      map.setView(coords, 18, {
        animate: true,
        duration: 1.5
      });
    }
  }, [coords, highlight, map]);

  return null;
};

const CampusMap: React.FC = () => {
  const routerLocation = useLocation();
  const [locations, setLocations] = useState<any[]>([]);
  const [selectedLocation, setSelectedLocation] = useState<any | null>(null);
  const [highlightedName, setHighlightedName] = useState<string | null>(null);
  const [highlightedRoom, setHighlightedRoom] = useState<string | null>(null);
  const [mapCenter, setMapCenter] = useState<[number, number]>([18.5204, 73.8567]); // Central campus point

  useEffect(() => {
    const fetchLocations = async () => {
      try {
        const response = await api.get('/locations');
        setLocations(response.data);

        // Check if navigation state has highlight data
        const state = routerLocation.state as { highlight?: string; room?: string };
        if (state && state.highlight) {
          setHighlightedName(state.highlight);
          if (state.room) {
            setHighlightedRoom(state.room);
          }
          
          // Find matching coordinates
          const matched = response.data.find(
            (loc: any) => loc.name.toLowerCase().includes(state.highlight!.toLowerCase())
          );
          if (matched) {
            setMapCenter([matched.latitude, matched.longitude]);
            setSelectedLocation(matched);
          }
        }
      } catch (err) {
        console.error('Error fetching campus locations:', err);
      }
    };

    fetchLocations();
  }, [routerLocation]);

  const handleMarkerClick = (loc: any) => {
    setSelectedLocation(loc);
    setHighlightedName(null);
    setHighlightedRoom(null);
  };

  return (
    <div className="flex-1 flex flex-col h-[calc(100vh-4rem)] md:h-screen bg-slate-50/50 dark:bg-dark-950 transition-colors duration-300">
      
      {/* Top Banner details */}
      <div className="px-6 py-4 bg-white dark:bg-dark-900 border-b border-slate-200/60 dark:border-slate-800/60 flex items-center justify-between transition-colors shadow-sm shrink-0">
        <div>
          <p className="text-xs font-bold text-brand-600 dark:text-brand-400 uppercase tracking-wider">Campus Directory</p>
          <h3 className="font-extrabold text-slate-800 dark:text-white">Interactive Campus Map</h3>
        </div>
        {highlightedName && (
          <div className="px-3.5 py-1.5 rounded-2xl bg-pink-50 dark:bg-pink-950/20 text-pink-700 dark:text-pink-400 border border-pink-100 dark:border-pink-950/30 text-xs font-bold flex items-center gap-1.5 animate-pulse">
            <Navigation size={14} className="animate-spin-slow" />
            <span>Showing Location: {highlightedRoom ? `${highlightedName} (${highlightedRoom})` : highlightedName}</span>
          </div>
        )}
      </div>

      {/* Map Content */}
      <div className="flex-1 flex flex-col lg:flex-row p-6 gap-6 relative min-h-0">
        
        {/* Left Side: Map Container */}
        <div className="flex-1 h-[300px] lg:h-full bg-slate-200 rounded-3xl overflow-hidden border border-slate-200/50 dark:border-slate-800/40 shadow-sm relative">
          <MapContainer 
            center={mapCenter} 
            zoom={16.5} 
            maxZoom={19}
            minZoom={15}
            scrollWheelZoom={true}
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              className="map-tiles dark:opacity-75 dark:invert"
            />
            
            {/* Map Controller */}
            <MapController coords={mapCenter} highlight={highlightedName} />

            {/* Markers */}
            {locations.map((loc) => {
              const isHighlighted = highlightedName && loc.name.toLowerCase().includes(highlightedName.toLowerCase());
              const isSelected = selectedLocation && selectedLocation.id === loc.id;
              
              // Standard blue color, custom pins
              let markerColor = 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)';
              if (loc.name === 'Library') markerColor = '#8b5cf6'; // Violet
              if (loc.name === 'Canteen') markerColor = '#f59e0b'; // Amber
              if (loc.name === 'Medical Center') markerColor = '#ef4444'; // Red
              if (loc.name === 'Sports Ground') markerColor = '#10b981'; // Emerald
              
              return (
                <Marker
                  key={loc.id}
                  position={[loc.latitude, loc.longitude]}
                  icon={isHighlighted ? highlightedIcon : createCustomIcon(markerColor)}
                  eventHandlers={{
                    click: () => handleMarkerClick(loc),
                  }}
                >
                  <Popup>
                    <div className="text-left font-sans">
                      <h4 className="font-extrabold text-sm text-slate-800 dark:text-slate-100">{loc.name}</h4>
                      <p className="text-[10px] text-slate-400 mt-0.5">Open until: {loc.open_until}</p>
                      <div className="flex items-center gap-1.5 mt-2">
                        <div className="w-1.5 h-1.5 bg-brand-500 rounded-full"></div>
                        <span className="text-xs font-bold text-brand-600 dark:text-brand-400">Occupancy: {loc.occupancy_pct}%</span>
                      </div>
                    </div>
                  </Popup>
                </Marker>
              );
            })}
          </MapContainer>
        </div>

        {/* Right Side: Location Info Pane */}
        <div className="w-full lg:w-80 shrink-0 bg-white dark:bg-dark-900 border border-slate-200/50 dark:border-slate-800/40 rounded-3xl p-6 shadow-sm flex flex-col justify-between space-y-6">
          {selectedLocation ? (
            <div className="space-y-6 flex-1 flex flex-col justify-between">
              <div className="space-y-5">
                <div className="flex items-start gap-4">
                  <div className="p-3 bg-brand-500/10 text-brand-600 dark:text-brand-400 rounded-2xl">
                    <Building size={24} />
                  </div>
                  <div>
                    <h4 className="font-black text-xl text-slate-800 dark:text-slate-100">{selectedLocation.name}</h4>
                    <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-slate-100 dark:bg-dark-800 text-slate-500 dark:text-slate-400 mt-1">
                      Fictional Coordinates
                    </span>
                  </div>
                </div>

                <div className="h-[1px] bg-slate-100 dark:bg-slate-800"></div>

                <div className="space-y-4">
                  {/* Hours */}
                  <div className="flex items-center justify-between text-sm">
                    <span className="flex items-center gap-2 text-slate-500"><Clock size={16} className="text-brand-500" /> Operational Hours</span>
                    <span className="font-bold text-slate-800 dark:text-slate-200">Until {selectedLocation.open_until}</span>
                  </div>

                  {/* Occupancy */}
                  <div className="space-y-1.5">
                    <div className="flex items-center justify-between text-sm">
                      <span className="flex items-center gap-2 text-slate-500"><Activity size={16} className="text-brand-500" /> Current Occupancy</span>
                      <span className="font-bold text-slate-800 dark:text-slate-200">{selectedLocation.occupancy_pct}%</span>
                    </div>
                    <div className="w-full bg-slate-100 dark:bg-dark-800 rounded-full h-1.5 overflow-hidden">
                      <div 
                        className={`h-full rounded-full ${
                          selectedLocation.occupancy_pct > 80 ? 'bg-red-500' : selectedLocation.occupancy_pct > 50 ? 'bg-amber-500' : 'bg-emerald-500'
                        }`} 
                        style={{ width: `${selectedLocation.occupancy_pct}%` }}
                      ></div>
                    </div>
                  </div>

                  {/* Study Rooms */}
                  {selectedLocation.study_rooms > 0 && (
                    <div className="flex items-center justify-between text-sm">
                      <span className="flex items-center gap-2 text-slate-500"><BookOpen size={16} className="text-brand-500" /> Study Rooms</span>
                      <span className="font-bold text-slate-800 dark:text-slate-200">{selectedLocation.study_rooms} rooms</span>
                    </div>
                  )}
                </div>

                <div className="h-[1px] bg-slate-100 dark:bg-slate-800"></div>

                {/* Description info */}
                <div className="space-y-1.5">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Facility Details</span>
                  <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed font-medium">
                    {selectedLocation.details}
                  </p>
                </div>
              </div>

              {highlightedRoom && selectedLocation.name.toLowerCase().includes(highlightedName!.toLowerCase()) && (
                <div className="p-4 bg-pink-50 dark:bg-pink-950/20 border border-pink-100 dark:border-pink-900/30 rounded-2xl">
                  <p className="text-[10px] font-extrabold uppercase text-pink-600 dark:text-pink-400 tracking-wider">Target Room Found</p>
                  <p className="text-xs text-slate-600 dark:text-slate-300 font-bold mt-1">
                    Room {highlightedRoom} is located on floor 2 of {selectedLocation.name}. Use the elevator or stairs.
                  </p>
                </div>
              )}
            </div>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-center text-slate-400 space-y-2">
              <Building size={36} className="text-slate-300 dark:text-dark-800 animate-pulse" />
              <p className="text-sm font-semibold">Select a building pin on the map to display operational details and active occupancy metrics.</p>
            </div>
          )}

          <div className="text-[10px] font-semibold text-slate-400 text-center leading-normal">
            Map tiles provided by OpenStreetMap. Latency synced with simulated campus IoT sensors.
          </div>
        </div>

      </div>
    </div>
  );
};

export default CampusMap;
