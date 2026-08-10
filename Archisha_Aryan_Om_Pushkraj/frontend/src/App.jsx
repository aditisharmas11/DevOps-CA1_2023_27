import React from 'react'
import './App.css'
import Navbar from './components/navbar.jsx'
import Hero from './components/hero.jsx'
import Features from './components/features.jsx'
import About from './components/about.jsx'
import MapSection from './components/maps.jsx'
import Footer from './components/footer.jsx'

function App() {
  return (
    <>
      <Navbar />
      <Hero />
      <About />
      <Features />
      <MapSection />
      <Footer />
    </>
  )
}

export default App
