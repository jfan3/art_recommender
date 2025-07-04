'use client';

import { useState, useEffect, useRef } from 'react';
import { FiSend } from 'react-icons/fi';
import { Toaster, toast } from 'react-hot-toast';
import SwipeFlow from './SwipeFlow';
import FunkyCharacter from './FunkyCharacter';

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
  const [characterActive, setCharacterActive] = useState(false);
  const initializationRef = useRef(false);

  useEffect(() => {
    // Check if already initialized to prevent double execution
    if (initializationRef.current) return;
    initializationRef.current = true;
    
    // Check if we have an existing completed profile
    const existingProfileComplete = localStorage.getItem('profilingComplete');
    const existingUserUuid = localStorage.getItem('userUuid');
    
    if (existingProfileComplete === 'true' && existingUserUuid) {
      // Restore completed state
      setUserUuid(existingUserUuid);
      setProfilingComplete(true);
      return;
    }
    
    // Otherwise start fresh: clear any previous session/profile
    localStorage.removeItem('userUuid');
    localStorage.removeItem('sessionId');
    localStorage.removeItem('profilingComplete');

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
                                if (prev.length === 0) {
                                    return [{ role: 'assistant', content: data.content }];
                                }
                                const lastMessage = prev[prev.length - 1];
                                if (lastMessage.role === 'assistant') {
                                    const updatedLastMessage = { ...lastMessage, content: lastMessage.content + data.content };
                                    return [...prev.slice(0, -1), updatedLastMessage];
                                } else {
                                    return [...prev, { role: 'assistant', content: data.content }];
                                }
                            });
                        } else if (data.type === 'complete') {
                            toast.success("Profiling complete!");
                            setProfilingComplete(true);
                            localStorage.setItem('profilingComplete', 'true');
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
                            setProfilingComplete(true);
                            localStorage.setItem('profilingComplete', 'true');
                            setIsLoading(false);
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
          console.log('Profile status:', profile);
          if (profile.complete) {
            console.log('Profile is complete, transitioning to SwipeFlow');
            setProfilingComplete(true);
            localStorage.setItem('profilingComplete', 'true');
            toast.success("Profile completed!");
            clearInterval(interval);
          }
        })
        .catch(err => {
          console.error('Error checking profile:', err);
        });
    }, 1500);
    return () => clearInterval(interval);
  }, [userUuid, profilingComplete]);

  // Handle character interaction
  const handleCharacterInteraction = (characterMessage: string) => {
    const characterBotMessage: Message = { role: 'assistant', content: characterMessage };
    setMessages(prev => [...prev, characterBotMessage]);
    setCharacterActive(true);
    
    // Auto-scroll to new message
    setTimeout(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, 100);
  };

  if (profilingComplete && userUuid) {
    return (
      <div className="relative">
        <SwipeFlow userUuid={userUuid} />
      </div>
    );
  }
  if (!userUuid) {
    return <div>Loading...</div>;
  }

  return (
    <>
      <Toaster position="top-center" />
      <div className="flex flex-row gap-1 w-full max-w-4xl mx-auto px-4 h-full">
        {/* Character Panel - 1/3 width */}
        <div className="flex flex-col justify-center items-center w-1/3">
          <FunkyCharacter 
            onInteraction={handleCharacterInteraction}
            isActive={characterActive}
          />
        </div>
        
        {/* Chat Panel - smaller size */}
        <div className="flex flex-col w-1/2 max-w-sm h-[45vh] relative overflow-hidden"
             style={{
               marginTop: '20px !important',
               marginRight: '20px !important',
               background: 'linear-gradient(135deg, #fdf2f8 0%, #fefbf3 50%, #f0fdf4 100%) !important',
               transform: 'translateY(20px) translateX(-30px)',
               border: '4px solid var(--color-primary-black)',
               borderRadius: '20px',
               boxShadow: '8px 8px 0px var(--color-primary-black)'
             }}>
        
        {/* Chat header */}
        <div className="px-2 py-3 text-center border-b border-gray-400"
             style={{
               background: '#fdf2f8',
               borderRadius: '20px 20px 0 0'
             }}>
          <h3 className="font-bold text-base arteme-title">
Chat with Arteme
          </h3>
        </div>
        
        <div className="flex-1 px-6 py-4 overflow-y-auto">
          {messages.map((msg, index) => (
            <div key={index} className={`flex mb-4 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`${msg.role === 'user' ? 'arteme-speech-bubble-user' : 'arteme-speech-bubble-assistant'}`}>
                {msg.content ? (
                  <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                ) : (
                  msg.role === 'assistant' && isLoading && (
                    <div className="arteme-loading-dots">
                      <div className="arteme-loading-dot"></div>
                      <div className="arteme-loading-dot"></div>
                      <div className="arteme-loading-dot"></div>
                    </div>
                  )
                )}
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>
        
        <form onSubmit={handleSendMessage} className="px-6 py-3 border-t border-midnight-black/10">
          <div className="flex items-center gap-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={isLoading ? "Creating magic..." : "What's your creative mood?"}
              className="arteme-input flex-1 disabled:opacity-50 text-sm"
              disabled={isLoading}
            />
            <button 
              type="submit" 
              disabled={isLoading} 
              className="arteme-button arteme-button-primary flex items-center gap-1 disabled:opacity-50 disabled:cursor-not-allowed text-sm px-3 py-2"
            >
              <FiSend className="text-base" />
              <span>Send</span>
            </button>
          </div>
        </form>
        </div>
      </div>
    </>
  );
} 