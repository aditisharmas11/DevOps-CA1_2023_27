import React from 'react';
import Navbar from './navbar.jsx';

function Hero() {
  const handleGetStartedClick = () => {
    const farmAnalysisSection = document.getElementById('farm-analysis-section');
    if (farmAnalysisSection) {
      farmAnalysisSection.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <div className='bg-[url(./assets/sunn3.jpg)] rounded-3xl bg-cover m-4 p-3'>
      <Navbar />
      <div className='flex justify-between'>
        <div className='pt-5'>
          <h1 className='text-7xl pt-6 px-8 font-medium text-shadow-lg text-white'> Unlock Optimal Crop Yield with AI-Powered Precision. </h1>
          <button
            className='text-black-700 text-xl py-3 px-8 mx-8 my-8 border bg-white border-black-500 rounded-4xl hover:bg-green-200 hover:shadow-xl/50'
            onClick={handleGetStartedClick}
          >
            Get Started
          </button>
        </div>
        <div className='card'>
          <div className='p-5 m-8 w-64 bg-[#c0fccc] border border-[#c0fccc] rounded-2xl shadow-sm'>
            <h5 className="mb-2 text-6xl text-black font">Draw</h5>
            <p className="mb-2 text-xl text-black font">your own farm </p>
            <p className="text-md text-black">and get personalized recommendations</p>
            <p className="text-md text-black">tailored especially for you! </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Hero;
