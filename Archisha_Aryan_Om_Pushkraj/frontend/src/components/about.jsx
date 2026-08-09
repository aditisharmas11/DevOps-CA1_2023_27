import React from 'react'
import image from '../assets/poly.jpg';

function About() {
  return (
    <div className='py-12'>
        <p className='text-5xl pb-7 px-8 font-medium'>   </p>
        <div className='bg-orange-100 px-3 py-6 flex justify-around'>
            <div class="basis-1/2 self-center pl-15" >
                <img className='h-90 w-130 rounded-4xl' src={image} alt="map" />
            </div>
            <div class="basis-1/2 self-center text-md pr-25">
                <p class="text-2xl font-bold pb-4"> About CultivAIte </p>
                <hr />
                <p class="p-3"> At CultivAIte, we are passionate about empowering farmers with intelligent tools to make informed decisions. Leveraging the power of Artificial Intelligence, advanced geospatial analysis, and machine learning, we provide optimized crop allocation recommendations tailored to your specific land and environmental conditions. </p>
                <p class="p-3"> Our mission is to promote efficient resource utilization, enhance crop yields, and contribute to sustainable agricultural practices. We understand the complexities of farming and strive to simplify the decision-making process by providing clear, data-driven insights and understandable explanations for our recommendations.</p>
              
            </div>
        </div>
    </div>
  )
}

export default About