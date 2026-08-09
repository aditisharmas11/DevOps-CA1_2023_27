
import React, { useState, useEffect } from 'react';
import useGoogleMaps from './hooks/useGoogleMaps';
import { geocodeCity } from '../services/geocodingService';

function MapSection() {
  const [city, setCity] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [polygonArea, setPolygonArea] = useState(null);
  const { map, drawingManager, geocoder, isLoaded, initMap, mapRef } = useGoogleMaps('AIzaSyB41DRUbKWJHPxaFjMAwdrzWzbVKartNGg');

  useEffect(() => {
    if (isLoaded && mapRef.current) {
      const mapOptions = {
        center: { lat: 20.5937, lng: 78.9629 }, // Default to India
        zoom: 5,
      };
      initMap(mapRef.current, mapOptions);

      if (drawingManager) {
        window.google.maps.event.addListener(drawingManager, 'polygoncomplete', (polygon) => {
          const area = window.google.maps.geometry.spherical.computeArea(polygon.getPath());
          setPolygonArea(area);
          polygon.setMap(null); // Remove the polygon after calculation
        });
      }
    }
  }, [isLoaded, drawingManager]);

  const handleCitySearch = async () => {
    if (!city || !geocoder) return;
    
    try {
      const location = await geocodeCity(geocoder, city + ', India');
      map.setCenter(location);
      map.setZoom(14);
    } catch (error) {
      console.error('Error geocoding city:', error);
      alert('Could not find the city. Please try again.');
    }
  };

  const handleAnalyze = async () => {
    if (!polygonArea) {
      alert('Please draw your farm area first');
      return;
    }

    setIsLoading(true);
    
    try {
      const center = map.getCenter();
      const response = await fetch(`http://localhost:5173/location?latitude=${center.lat()}&longitude=${center.lng()}&district=${city}&state=&language=en`);
      const data = await response.json();
      setResults(data.llm_output);
    } catch (error) {
      console.error('Error fetching data:', error);
      alert('Failed to get crop recommendations');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className='py-12'>
      <p className='text-5xl pb-7 px-8 font-medium'>Farm Analysis</p>
      <div className='flex px-8 gap-8'>
        <div className='basis-2/3'>
          <div ref={mapRef} style={{ height: '500px', width: '100%', borderRadius: '20px' }} />
        </div>
        <div className='basis-1/3 flex flex-col gap-4'>
          <div className='bg-white p-6 rounded-2xl shadow-md'>
            <h3 className='text-2xl font-medium mb-4'>Enter Farm Location</h3>
            <div className='flex'>
              <input
                type='text'
                value={city}
                onChange={(e) => setCity(e.target.value)}
                placeholder='Enter city name'
                className='flex-grow p-2 border rounded-l-lg'
              />
              <button 
                onClick={handleCitySearch}
                className='bg-green-500 text-white p-2 rounded-r-lg hover:bg-green-600'
              >
                Search
              </button>
            </div>
            <p className='mt-4 text-sm text-gray-600'>
              After searching, draw your farm area on the map by clicking the polygon tool in the top center of the map.
            </p>
          </div>
          
          <div className='bg-white p-6 rounded-2xl shadow-md'>
            <h3 className='text-2xl font-medium mb-4'>Analyze Farm</h3>
            <button
              onClick={handleAnalyze}
              disabled={isLoading}
              className={`w-full p-3 rounded-lg ${isLoading ? 'bg-gray-400' : 'bg-blue-500 hover:bg-blue-600'} text-white`}
            >
              {isLoading ? (
                <div className='flex justify-center items-center'>
                  <div className='animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2'></div>
                  Analyzing...
                </div>
              ) : (
                'Analyze'
              )}
            </button>
            {polygonArea && (
              <p className='mt-4 text-sm'>
                Farm area: {(polygonArea / 10000).toFixed(2)} hectares
              </p>
            )}
          </div>
        </div>
      </div>
      
      {results && (
        <div className='mt-8 px-8'>
          <div className='bg-white p-6 rounded-2xl shadow-md'>
            <h3 className='text-2xl font-medium mb-4'>Crop Recommendations</h3>
            <div className='whitespace-pre-line'>{results}</div>
          </div>
        </div>
      )}
    </div>
  );
}

export default MapSection;
