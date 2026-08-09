import React from 'react'


function Features() {
  return (
    <div className='pb-18'>
        <p className='text-5xl pb-7 px-8 font-medium'>  Features </p>
        <div className='px-8 py-6 flex justify-around gap-8'>
            <div class="basis-1/3 bg-green-100 px-5 py-6 rounded-3xl">
                <div> 
                    <p class="text-2xl font-medium pb-3"> AI-Powered Optimization </p>
                    <p> Our sophisticated AI algorithms analyze your plot area and location-specific agricultural characteristics to generate the most efficient crop allocation strategies. </p>
                </div>
            </div>
            <div class="basis-1/3 bg-green-100 px-8 py-6 rounded-3xl">
                <div> 
                    <p class="text-2xl font-medium pb-3"> Geospatial Precision </p>
                    <p> We integrate advanced geospatial analysis to understand your land's unique properties, ensuring area-specific crop distribution for optimal resource use. </p>
                </div>
            </div>
            <div class="basis-1/3 bg-green-100 px-8 py-6 rounded-3xl">
                <div> 
                    <p class="text-2xl font-medium pb-3"> Intelligent Explanations </p>
                    <p> Our integrated Large Language Model provides detailed explanations for each crop allocation decision, outlining the environmental factors and user preferences considered. </p>
                </div>
            </div>
           
        </div>
    </div>
  )
}

export default Features