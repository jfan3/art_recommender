'use client';

import { useState, useEffect, useRef } from 'react';
import { FiSend } from 'react-icons/fi';
import { Toaster, toast } from 'react-hot-toast';
import SwipeFlow from './SwipeFlow';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

const API_BASE_URL = 'http://localhost:8080';

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [userUuid, setUserUuid] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [profilingComplete, setProfilingComplete] = useState(false);

  useEffect(() => {
    // Always start fresh: clear any previous session/profile
    localStorage.removeItem('userUuid');
    localStorage.removeItem('sessionId');

    // Immediately create a new profile and start chat
    const startConversation = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/profiles`, { method: 'POST' });
        if (!response.ok) {
          throw new Error('Failed to create profile.');
        }
        const data = await response.json();
        setUserUuid(data.uuid);
        localStorage.setItem('userUuid', data.uuid);
        const newSessionId = `frontend-session-${Date.now()}`;
        setSessionId(newSessionId);
        localStorage.setItem('sessionId', newSessionId);
        toast.success('New profile created!');
        // Send initial message to get the conversation started
        const initialBotMessage: Message = { role: 'assistant', content: '' };
        setMessages([initialBotMessage]);
        setIsLoading(true);
        const payload = {
            session_id: newSessionId,
            messages: [{ role: 'user', content: 'Hi' }],
            user_uuid: data.uuid,
        };
        const chatResponse = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Accept': 'text/event-stream' },
            body: JSON.stringify(payload),
        });
        if (!chatResponse.body) return;
        const reader = chatResponse.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        while (true) {
            const { done, value } = await reader.read();
            if (done) {
                setIsLoading(false);
                break;
            }
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const dataStr = line.substring(6);
                    try {
                        const data = JSON.parse(dataStr);
                        if (data.type === 'content') {
                            setMessages(prev => {
                                const lastMessage = prev[prev.length - 1];
                                const updatedLastMessage = { ...lastMessage, content: lastMessage.content + data.content };
                                return [...prev.slice(0, -1), updatedLastMessage];
                            });
                        } else if (data.type === 'complete') {
                            toast.success("Profiling complete!");
                            setProfilingComplete(true);
                            setIsLoading(false);
                        }
                    } catch (e) {
                        console.error('Failed to parse stream data:', e);
                    }
                }
            }
        }
      } catch (error) {
        toast.error('Could not connect to the agent. Is the backend running?');
        console.error(error);
      }
    };
    startConversation();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading || !sessionId || !userUuid) return;

    const userMessage: Message = { role: 'user', content: input };
    const newMessages: Message[] = [...messages, userMessage, { role: 'assistant', content: '' }];
    setMessages(newMessages);
    setInput('');
    setIsLoading(true);

    try {
        const payload = {
            session_id: sessionId,
            messages: [{ role: 'user', content: input }],
            user_uuid: userUuid,
        };

        const response = await fetch(`${API_BASE_URL}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Accept': 'text/event-stream' },
            body: JSON.stringify(payload),
        });

        if (!response.body) return;

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) {
                setIsLoading(false);
                break;
            }
            
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const dataStr = line.substring(6);
                    try {
                        const data = JSON.parse(dataStr);
                        if (data.type === 'content') {
                             setMessages(prev => {
                                const lastMessage = prev[prev.length - 1];
                                const updatedLastMessage = { ...lastMessage, content: lastMessage.content + data.content };
                                return [...prev.slice(0, -1), updatedLastMessage];
                            });
                        } else if (data.type === 'complete') {
                            toast.success("Profiling complete!");
                            setIsLoading(true);
                        }
                    } catch (e) {
                        console.error('Failed to parse stream data:', e);
                    }
                }
            }
        }
    } catch (error) {
        toast.error('Failed to send message.');
        console.error(error);
        setIsLoading(false);
        setMessages(prev => prev.slice(0, -1)); // Remove the empty assistant message
    }
  };

  // Poll for profile completion after chat stream finishes
  useEffect(() => {
    if (!userUuid || profilingComplete) return;
    const interval = setInterval(() => {
      fetch(`${API_BASE_URL}/profiles/${userUuid}`)
        .then(res => res.json())
        .then(profile => {
          if (profile.complete) {
            setProfilingComplete(true);
            clearInterval(interval);
          }
        });
    }, 1500);
    return () => clearInterval(interval);
  }, [userUuid, profilingComplete]);

  if (profilingComplete && userUuid) {
    return <SwipeFlow userUuid={userUuid} />;
  }
  if (!userUuid) {
    return <div>Loading...</div>;
  }

  return (
    <>
      <Toaster position="top-center" />
      <div className="flex flex-col w-full max-w-2xl h-[70vh] bg-gray-800 rounded-lg shadow-lg">
        <div className="flex-1 p-4 overflow-y-auto">
          {messages.map((msg, index) => (
            <div key={index} className={`flex mb-4 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`px-4 py-2 rounded-lg max-w-prose ${msg.role === 'user' ? 'bg-blue-600' : 'bg-gray-700'}`}>
                <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
              </div>
            </div>
          ))}
           {isLoading && messages[messages.length - 1]?.role === 'assistant' && (
             <div className="flex justify-start mb-4">
                <div className="px-4 py-2 rounded-lg bg-gray-700">
                    <div className="flex items-center justify-center">
                        <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                        <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce [animation-delay:-0.15s] mx-1"></div>
                        <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce"></div>
                    </div>
                </div>
            </div>
           )}
          <div ref={messagesEndRef} />
        </div>
        <form onSubmit={handleSendMessage} className="p-4 border-t border-gray-700 flex items-center">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={isLoading ? "Waiting for response..." : "Type your message..."}
            className="w-full px-4 py-2 bg-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
            disabled={isLoading}
          />
          <button type="submit" disabled={isLoading} className="ml-2 p-2 rounded-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed">
            <FiSend className="text-white" />
          </button>
        </form>
      </div>
    </>
  );
} 