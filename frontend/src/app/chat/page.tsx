'use client';

import Chat from '@/components/Chat';

export default function ChatPage() {
  return (
    <main 
      className="min-h-screen flex flex-col items-center justify-start p-4 lg:p-8"
      style={{
        background: `var(--color-primary-red)`
      }}
    >
      <div className="text-center mb-6 lg:mb-8 relative z-10 w-full">
        <h1 className="text-4xl lg:text-6xl arteme-title mb-4 lg:mb-6" style={{ color: 'var(--color-primary-white)' }}>
          ARTEME
        </h1>
        <div className="arteme-header mb-4 text-sm lg:text-base" style={{ 
          backgroundColor: 'var(--color-primary-yellow)', 
          color: 'var(--color-primary-black)',
          border: '4px solid var(--color-primary-black)',
          boxShadow: '6px 6px 0px var(--color-primary-black)',
          padding: '8px 16px lg:padding-original'
        }}>
          Your Art Buddy
        </div>
        <div className="arteme-accent-bar w-24 lg:w-32 mx-auto"></div>
      </div>
      
      <div className="flex-1 w-full flex items-center justify-center">
        <Chat />
      </div>
    </main>
  );
}