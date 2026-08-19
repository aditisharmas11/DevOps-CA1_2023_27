# ZenGen - Teen Mental Health Platform

ZenGen is a web-based mental health support platform designed for teenagers. 
It provides a structured assessment system along with AI-powered support to help users understand their mental well-being.

## Features

- **Mental Health Assessment**: Users complete a questionnaire to evaluate mood, anxiety, and social well-being
- **Rule-Based Analysis**: The system calculates scores and classifies users into Low, Moderate, or High Risk categories
- **AI-Generated Summary**: Personalized feedback is generated using Google Gemini API
- **AI Chatbot**: Provides supportive and context-aware responses for users
- **User History**: Stores previous assessments for tracking mental health trends

---

## Technology Stack

- **Frontend**: React, TypeScript, TailwindCSS  
- **Backend**: Node.js, Express  
- **Database**: PostgreSQL  
- **AI Integration**: Google Gemini API  

---

## System Overview

ZenGen follows a client-server architecture:

1. User interacts with the React frontend  
2. Data is sent to the Node.js backend  
3. Backend applies rule-based scoring logic  
4. Results are processed and stored in PostgreSQL  
5. Google Gemini API generates summary and chatbot responses  
6. Output is displayed to the user  

---

## Key Design Approach

- The system uses **rule-based logic** for prediction  
- No machine learning model is trained in the main system  
- AI is used only for generating natural language responses  

---

## Running the Project

1. Install dependencies:
   ```bash
   npm install

Set environment variables:

GEMINI_API_KEY=your_api_key_here
DATABASE_URL=your_database_url
SESSION_SECRET=your_secret_key

Run the project:

npx tsx server/index.ts

Open:

http://localhost:5000
Project Structure
zengen/
├── client/       # React frontend
├── server/       # Node.js backend
├── shared/       # Shared schema
Note

ZenGen is designed as a mental health awareness and support tool.
It does not provide clinical diagnosis and should not replace professional medical advice.


