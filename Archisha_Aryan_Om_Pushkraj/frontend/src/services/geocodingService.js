export const geocodeCity = async (geocoder, city) => {
  return new Promise((resolve, reject) => {
    geocoder.geocode({ address: city }, (results, status) => {
      if (status === 'OK' && results[0]) {
        const location = results[0].geometry.location;
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

        resolve({
          lat: location.lat(),
          lng: location.lng(),
          district,
          state,
          formattedAddress: results[0].formatted_address
        });
      } else {
        reject(new Error(`Geocode failed: ${status}`));
      }
    });
  });
};
