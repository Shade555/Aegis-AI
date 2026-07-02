import React, { useState } from 'react';

export default function Home() {
  const [htmlContent, setHtmlContent] = useState('');
  const API_KEY = "AKIAIOSFODNN7EXAMPLE"; // VULNERABILITY: Hardcoded frontend API key

  return (
    <div>
      <h1>Vulnerable React Component</h1>
      
      {/* VULNERABILITY: DOM-based XSS through dangerouslySetInnerHTML */}
      <div dangerouslySetInnerHTML={{ __html: htmlContent }} />
      
      <input 
        type="text" 
        onChange={(e) => setHtmlContent(e.target.value)} 
        placeholder="Enter HTML"
      />

      {/* VULNERABILITY: Using hardcoded key in request */}
      <button onClick={() => fetch(`https://api.example.com/data?key=${API_KEY}`)}>
        Fetch Data
      </button>
    </div>
  );
}
