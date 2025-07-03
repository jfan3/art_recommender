'use client';

import Link from 'next/link';

export default function Home() {
  return (
    <main className="min-h-screen overflow-hidden relative" style={{ background: 'var(--color-primary-red)' }}>
      
      {/* Character Legs at Top */}
      <div className="absolute top-0 left-1/2 transform -translate-x-1/2 z-10">
        <img 
          src="/assets/character.png" 
          alt="ARTEME Character Legs"
          className="w-80 h-80 object-contain"
          style={{
            clipPath: 'inset(65% 0 0 0)', // Only show bottom 35% of the image (legs and boots)
            filter: 'brightness(1.1) contrast(1.2) saturate(1.6)',
            transform: 'translateY(-75%)', // Move the legs up higher for better spacing
            objectPosition: 'center bottom'
          }}
        />
      </div>
      
      {/* Main Content - Centered */}
      <section className="relative min-h-screen flex flex-col items-center justify-center px-8 py-16">
        
        {/* Main content */}
        <div className="text-center relative z-20 max-w-4xl mt-32">
          
          <h1 className="text-7xl md:text-8xl lg:text-9xl arteme-title mb-8" style={{ color: 'var(--color-primary-white)' }}>
            ARTEME
          </h1>
          
          <div className="arteme-header text-2xl md:text-3xl lg:text-4xl mb-8 inline-block" style={{ 
            backgroundColor: 'var(--color-primary-white)', 
            color: 'var(--color-primary-black)',
            border: '4px solid var(--color-primary-black)',
            boxShadow: '8px 8px 0px var(--color-primary-black)',
            padding: '16px 32px'
          }}>
            PERSONALIZED ART JOURNEY
          </div>
          
          <p className="text-xl md:text-2xl lg:text-3xl mb-12 font-bold" style={{ color: 'var(--color-primary-white)' }}>
            Taste is not random. We map yours.
          </p>
          
          <div className="arteme-accent-bar w-48 mx-auto mb-12"></div>
          
          <Link href="/chat" className="relative z-50 inline-block">
            <button className="arteme-button arteme-button-primary text-xl md:text-2xl px-12 py-6 transform hover:scale-105 transition-all duration-300 relative z-50 pointer-events-auto">
              START MY JOURNEY
            </button>
          </Link>
        </div>
      </section>
    </main>
  );
}
