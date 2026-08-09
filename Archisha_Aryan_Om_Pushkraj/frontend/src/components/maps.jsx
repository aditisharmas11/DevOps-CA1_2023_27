import React, { useState, useEffect, useRef } from 'react';
import { geocodeCity } from '../services/geocodingService';
import './MapSection.css'; 

const MapSection = () => {
  const [city, setCity] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState('');
  const [polygonArea, setPolygonArea] = useState(null);
  const [language, setLanguage] = useState('english');
  const mapRef = useRef(null);
  const drawingManagerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const currentPolygonRef = useRef(null);
  const locationDetailsRef = useRef({ district: '', state: '' });

  // Language options
  const languages = [
    { value: 'english', label: 'English' },
    { value: 'hindi', label: 'Hindi' },
    { value: 'assamese', label: 'Assamese' },
    { value: 'bengali', label: 'Bengali' },
    { value: 'bodo', label: 'Bodo' },
    { value: 'dogri', label: 'Dogri' },
    { value: 'gujarati', label: 'Gujarati' },
    { value: 'kannada', label: 'Kannada' },
    { value: 'kashmiri', label: 'Kashmiri' },
    { value: 'konkani', label: 'Konkani' },
    { value: 'maithili', label: 'Maithili' },
    { value: 'malayalam', label: 'Malayalam' },
    { value: 'manipuri', label: 'Manipuri' },
    { value: 'marathi', label: 'Marathi' },
    { value: 'odia', label: 'Odia' },
    { value: 'punjabi', label: 'Punjabi' },
    { value: 'sanskrit', label: 'Sanskrit' },
    { value: 'santali', label: 'Santali' },
    { value: 'tamil', label: 'Tamil' },
    { value: 'telugu', label: 'Telugu' },
    { value: 'urdu', label: 'Urdu' },
  ];

  useEffect(() => {
    const script = document.createElement('script');
    script.src = `https://maps.googleapis.com/maps/api/js?key=AIzaSyB41DRUbKWJHPxaFjMAwdrzWzbVKartNGg&libraries=drawing,places,geocoder&callback=initMap`;
    script.async = true;
    script.defer = true;
    document.head.appendChild(script);

    window.initMap = initMap;

    return () => {
      document.head.removeChild(script);
      delete window.initMap;
      if (mapInstanceRef.current) {
        window.google.maps.event.clearInstanceListeners(mapInstanceRef.current);
      }
    };
  }, []);

  const initMap = () => {
    const map = new window.google.maps.Map(mapRef.current, {
      center: { lat: 20.5937, lng: 78.9629 },
      zoom: 5,
    });

    mapInstanceRef.current = map;

    const drawingManager = new window.google.maps.drawing.DrawingManager({
      drawingMode: null,
      drawingControl: true,
      drawingControlOptions: {
        position: window.google.maps.ControlPosition.TOP_CENTER,
        drawingModes: [window.google.maps.drawing.OverlayType.POLYGON],
      },
      polygonOptions: {
        fillColor: '#00FF00',
        fillOpacity: 0.3,
        strokeWeight: 2,
        clickable: false,
        editable: true,
        zIndex: 1,
      },
    });

    drawingManager.setMap(map);
    drawingManagerRef.current = drawingManager;

    window.google.maps.event.addListener(drawingManager, 'polygoncomplete', (polygon) => {
      if (currentPolygonRef.current) {
        currentPolygonRef.current.setMap(null);
      }
      currentPolygonRef.current = polygon;

      // Calculate area
      const area = window.google.maps.geometry.spherical.computeArea(polygon.getPath());
      setPolygonArea(area);

      // Get location details
      const bounds = new window.google.maps.LatLngBounds();
      polygon.getPath().forEach((latLng) => bounds.extend(latLng));
      const center = bounds.getCenter();

      const geocoder = new window.google.maps.Geocoder();
      geocoder.geocode({ location: center }, (results, status) => {
        if (status === 'OK' && results[0]) {
          let district = '';
          let state = '';

          for (const component of results[0].address_components) {
            if (component.types.includes('administrative_area_level_2')) {
              district = component.long_name;
            }
            if (component.types.includes('administrative_area_level_1')) {
              state = component.long_name;
            }
          }

          setCity(results[0].formatted_address);
          locationDetailsRef.current = { district, state };
        }
      });
    });
  };

  const handleCitySearch = async () => {
    if (!city.trim()) return;

    setIsLoading(true);
    try {
      const geocoder = new window.google.maps.Geocoder();
      const locationData = await geocodeCity(geocoder, city);
      mapInstanceRef.current.setCenter({ lat: locationData.lat, lng: locationData.lng });
      mapInstanceRef.current.setZoom(14);
      setCity(locationData.formattedAddress);
      locationDetailsRef.current = { district: locationData.district, state: locationData.state };
    } catch (error) {
      console.error('Geocoding error:', error);
      alert('Could not find the location. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAnalyze = async () => {
    if (!currentPolygonRef.current && !city.trim()) {
      alert('Please draw your farm area on the map or search for a location first.');
      return;
    }

    setIsLoading(true);
    setResults('');

    try {
      let latitude, longitude, district, state;

      if (currentPolygonRef.current) {
        const bounds = new window.google.maps.LatLngBounds();
        currentPolygonRef.current.getPath().forEach((latLng) => bounds.extend(latLng));
        const center = bounds.getCenter();
        latitude = center.lat();
        longitude = center.lng();
        district = locationDetailsRef.current.district;
        state = locationDetailsRef.current.state;
      } else if (city.trim()) {
        const geocoder = new window.google.maps.Geocoder();
        const locationData = await geocodeCity(geocoder, city);
        latitude = locationData.lat;
        longitude = locationData.lng;
        district = locationData.district;
        state = locationData.state;
      } else {
        setIsLoading(false);
        alert('Please select a location or draw a polygon.');
        return;
      }

      const response = await fetch(
        `http://localhost:5000/location?latitude=${latitude}&longitude=${longitude}&district=${encodeURIComponent(district)}&state=${encodeURIComponent(state)}&language=${language}`
      );
      const data = await response.json();
      setResults(data.llm_output);
    } catch (error) {
      console.error('Analysis error:', error);
      setResults('Error analyzing location: ' + error.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="map-section-container" id="farm-analysis-section">
      <h1 className="map-section-title">Farm Analysis Tool</h1>

      <div className="map-content-wrapper">
        <div className="map-container">
          <div ref={mapRef} className="google-map" />
        </div>

        <div className="controls-container">
          <div className="control-card">
            <h3 className="control-title">Location Settings</h3>
            <div className="search-container">
              <input
                type="text"
                value={city}
                onChange={(e) => setCity(e.target.value)}
                placeholder="Enter location or draw on map"
                className="location-input"
                onKeyPress={(e) => e.key === 'Enter' && handleCitySearch()}
              />
              <button
                onClick={handleCitySearch}
                disabled={isLoading || !city.trim()}
                className="search-button"
              >
                {isLoading ? 'Searching...' : 'Search'}
              </button>
            </div>

            <div className="language-selector">
              <label htmlFor="language-select">Output Language:</label>
              <select
                id="language-select"
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="language-dropdown"
              >
                {languages.map((lang) => (
                  <option key={lang.value} value={lang.value}>
                    {lang.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="control-card">
            <h3 className="control-title">Farm Analysis</h3>
            {polygonArea && (
              <p className="area-display">
                Farm Area: <strong>{(polygonArea / 10000).toFixed(2)} hectares</strong>
              </p>
            )}
            <button
              onClick={handleAnalyze}
              disabled={isLoading || (!currentPolygonRef.current && !city.trim())}
              className="analyze-button"
            >
              {isLoading ? (
                <>
                  <span className="spinner"></span>
                  Analyzing...
                </>
              ) : (
                'Analyze Farm'
              )}
            </button>
          </div>
        </div>
      </div>

      {results && (
        <div className="results-container">
          <h3 className="results-title">Crop Recommendations</h3>
          <div className="results-content">
            {results}
          </div>
        </div>
      )}
    </div>
  );
};

export default MapSection;
