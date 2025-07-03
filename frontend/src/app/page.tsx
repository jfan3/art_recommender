'use client';

import Link from 'next/link';

export default function Home() {
  return (
    <main className="min-h-screen overflow-x-hidden" style={{ background: 'var(--color-primary-red)' }}>
      
      {/* Hero Section */}
      <section className="relative min-h-screen flex flex-col items-center justify-center px-8 py-16">
        
        {/* Floating decorative elements */}
        <div className="absolute top-20 left-10 w-16 h-16 bg-yellow-400 rounded-full animate-bounce" style={{ animationDelay: '0s' }}></div>
        <div className="absolute top-32 right-16 w-8 h-8 bg-pink-500 rotate-45 animate-pulse" style={{ animationDelay: '1s' }}></div>
        <div className="absolute bottom-40 left-20 w-12 h-12 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '2s' }}></div>
        <div className="absolute top-1/3 right-1/4 w-6 h-6 bg-green-400" style={{ clipPath: 'polygon(50% 0%, 0% 100%, 100% 100%)', animation: 'spin 3s linear infinite' }}></div>
        
        {/* Main content */}
        <div className="text-center relative z-10 max-w-4xl">
          
          <h1 className="text-8xl md:text-9xl arteme-title mb-8 animate-pulse" style={{ color: 'var(--color-primary-white)' }}>
            ARTEME
          </h1>
          
          <div className="arteme-header text-2xl md:text-3xl mb-8 inline-block" style={{ 
            backgroundColor: 'var(--color-primary-white)', 
            color: 'var(--color-primary-black)',
            border: '4px solid var(--color-primary-black)',
            boxShadow: '8px 8px 0px var(--color-primary-black)',
            padding: '16px 32px'
          }}>
            EUPHORIA EMPIRE
          </div>
          
          <p className="text-xl md:text-2xl mb-12 font-bold" style={{ color: 'var(--color-primary-white)' }}>
            Where Art Meets Emotion<br/>
            Discover Your Creative Universe
          </p>
          
          <div className="arteme-accent-bar w-48 mx-auto mb-12"></div>
          
          <Link href="/chat">
            <button className="arteme-button arteme-button-primary text-xl px-12 py-6 transform hover:scale-105 transition-all duration-300">
              ENTER THE EMPIRE
            </button>
          </Link>
        </div>
      </section>
    </main>
  );
}
