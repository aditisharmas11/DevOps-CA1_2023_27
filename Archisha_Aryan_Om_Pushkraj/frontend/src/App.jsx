import React from 'react'
import './App.css'
import Hero from '../src/components/hero.jsx';
import Features from '../src/components/features.jsx';
import About from '../src/components/about.jsx';
import MapSection from '../src/components/maps.jsx';
import Footer from '../src/components/footer.jsx';

function App() {
  return (
    <>
      <Hero />
      <About />
      <Features />
      <MapSection />
      <Footer />
    </>
  )
}
export default App
