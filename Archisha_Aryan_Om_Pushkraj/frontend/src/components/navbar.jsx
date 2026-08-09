import React from 'react'
import logo from '../assets/Cultiv.svg';

function Navbar() {
  return (
    <div className='bg-white rounded-4xl mx-1 my-2 px-3 py-4 flex justify-center'>
        <img className='h-15 mx-4' src={logo} />
        {/* <div className='flex justify-center' >
            <img className='h-15 mx-4 align-center' src={logo} />
        </div> */}
        {/* <div className=''>
            <p className='text-xl px-4 py-1'> Link 1 </p>
            <p className='text-xl px-4 py-1'> Link 2 </p>
            <p className='text-xl px-4 py-1'> Link 3 </p>
            <p className='text-xl px-4 py-1'> Link 4 </p>
            <p className='text-xl px-4 py-1'> Link 5 </p>
        </div>
        <div className='flex'>
            <button className='text-black-700 py-2 px-8 mx-1 border border-black-500 rounded-4xl'> Log in </button>
            <button className='text-black-700 py-2 px-8 mx-1 border border-black-500 rounded-4xl'> Sign up </button>
        </div> */}
    </div>
  )
}

export default Navbar