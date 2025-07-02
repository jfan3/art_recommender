'use client';

import Chat from '@/components/Chat';

export default function Home() {
  return (
    <main 
      className="flex min-h-screen flex-col items-center justify-center p-12"
      style={{
        background: `var(--color-primary-red)`
      }}
    >
      <div className="text-center mb-12 relative z-10">
        <h1 className="text-7xl arteme-title mb-6" style={{ color: 'var(--color-primary-white)' }}>
          ARTEME
        </h1>
        <div className="arteme-header mb-4" style={{ 
          backgroundColor: 'var(--color-primary-white)', 
          color: 'var(--color-primary-black)',
          border: '4px solid var(--color-primary-black)',
          boxShadow: '6px 6px 0px var(--color-primary-black)'
        }}>
          DISCOVER YOUR ART SOUL
        </div>
        <div className="arteme-accent-bar w-32 mx-auto"></div>
      </div>
      
      <Chat />
    </main>
  );
}
