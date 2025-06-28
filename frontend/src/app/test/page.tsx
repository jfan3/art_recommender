'use client';

import { useState } from 'react';

export default function TestPage() {
  const [testResult, setTestResult] = useState<string>('');

  const testBackendConnection = async () => {
    try {
      const response = await fetch('http://localhost:8080/');
      if (response.ok) {
        const data = await response.json();
        setTestResult(`✅ Backend connected: ${data.message}`);
      } else {
        setTestResult(`❌ Backend error: ${response.status}`);
      }
    } catch (error) {
      setTestResult(`❌ Connection failed: ${error}`);
    }
  };

  const testProfileCreation = async () => {
    try {
      const response = await fetch('http://localhost:8080/profiles', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      if (response.ok) {
        const data = await response.json();
        setTestResult(`✅ Profile created: ${data.uuid}`);
      } else {
        setTestResult(`❌ Profile creation failed: ${response.status}`);
      }
    } catch (error) {
      setTestResult(`❌ Profile creation error: ${error}`);
    }
  };

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">Frontend Test Page</h1>
      <div className="space-y-4">
        <button 
          onClick={testBackendConnection}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Test Backend Connection
        </button>
        <button 
          onClick={testProfileCreation}
          className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 ml-2"
        >
          Test Profile Creation
        </button>
        {testResult && (
          <div className="mt-4 p-4 bg-gray-100 rounded">
            <pre>{testResult}</pre>
          </div>
        )}
      </div>
    </div>
  );
} 