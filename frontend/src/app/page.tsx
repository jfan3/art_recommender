'use client';

import Chat from '@/components/Chat';

export default function Home() {
  return (
    <main 
      className="flex min-h-screen flex-col items-center justify-center p-8"
      style={{
        background: `linear-gradient(135deg, 
          var(--color-neutral-beige) 0%, 
          rgba(211, 164, 255, 0.15) 25%, 
          rgba(255, 182, 193, 0.1) 50%, 
          rgba(255, 202, 43, 0.08) 75%, 
          var(--color-neutral-beige) 100%)`
      }}
    >
      <div className="text-center mb-12 relative z-10">
        <h1 className="text-7xl arteme-title mb-6">
          ARTEME
        </h1>
        <div className="arteme-header mb-4">
          START YOUR ART EMPIRE
        </div>
        <div className="arteme-accent-bar w-32 mx-auto"></div>
      </div>
      
      <Chat />
    </main>
  );
}
