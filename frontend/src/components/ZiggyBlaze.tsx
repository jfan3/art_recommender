import React, { useState, useEffect } from 'react';

interface ZiggyBlazeProps {
  isVisible?: boolean;
  celebrationType?: 'victory' | 'achievement' | 'discovery' | 'confidence';
  onAnimationComplete?: () => void;
}

const ZiggyBlaze: React.FC<ZiggyBlazeProps> = ({ 
  isVisible = false, 
  celebrationType = 'victory',
  onAnimationComplete 
}) => {
  const [currentAnimation, setCurrentAnimation] = useState('default');
  const [showCelebration, setShowCelebration] = useState(false);

  // Victory messages based on celebration type
  const celebrationMessages = {
    victory: [
      "YOU DID IT!",
      "AMAZING WORK!",
      "THAT'S THE SPIRIT!",
      "KEEP SHINING!"
    ],
    achievement: [
      "LEVEL UP!",
      "INCREDIBLE!",
      "YOU'RE ON FIRE!",
      "UNSTOPPABLE!"
    ],
    discovery: [
      "BRILLIANT FIND!",
      "ARTISTIC GENIUS!",
      "PERFECT CHOICE!",
      "TASTE MASTER!"
    ],
    confidence: [
      "OWN IT!",
      "BE BOLD!",
      "EXPRESS YOURSELF!",
      "CONFIDENCE KING!"
    ]
  };

  const [currentMessage, setCurrentMessage] = useState(
    celebrationMessages[celebrationType][0]
  );

  useEffect(() => {
    if (isVisible) {
      setShowCelebration(true);
      setCurrentAnimation('celebration');
      
      // Cycle through messages
      const messageInterval = setInterval(() => {
        const messages = celebrationMessages[celebrationType];
        setCurrentMessage(messages[Math.floor(Math.random() * messages.length)]);
      }, 800);

      // Auto-hide after 4 seconds
      const hideTimer = setTimeout(() => {
        setCurrentAnimation('exit');
        setTimeout(() => {
          setShowCelebration(false);
          onAnimationComplete?.();
        }, 500);
      }, 4000);

      return () => {
        clearInterval(messageInterval);
        clearTimeout(hideTimer);
      };
    }
  }, [isVisible, celebrationType, onAnimationComplete]);

  if (!showCelebration) return null;

  return (
    <div className={`fixed inset-0 z-50 flex items-center justify-center pointer-events-none ${
      currentAnimation === 'celebration' ? 'animate-fade-in' : 
      currentAnimation === 'exit' ? 'animate-fade-out' : ''
    }`}>
      
      {/* Background overlay */}
      <div className="absolute inset-0 bg-black/20"></div>
      
      {/* Ziggy Blaze Character */}
      <div className="relative z-10 flex flex-col items-center">
        
        {/* Character Container */}
        <div className={`relative ${
          currentAnimation === 'celebration' 
            ? 'animate-ziggy-celebration' 
            : 'animate-ziggy-default'
        }`} style={{ width: '200px', height: '280px' }}>
          
          {/* Blue Hat */}
          <div className="absolute top-0 left-1/2 transform -translate-x-1/2 w-24 h-8 bg-blue-500 rounded-full border-4 border-black">
            {/* Hat brim */}
            <div className="absolute -bottom-2 left-1/2 transform -translate-x-1/2 w-28 h-3 bg-blue-500 rounded-full border-2 border-black"></div>
            {/* Hat decorations */}
            <div className="absolute -top-2 left-2 w-6 h-4 bg-black rounded-full"></div>
            <div className="absolute -top-2 right-2 w-6 h-4 bg-black rounded-full"></div>
          </div>
          
          {/* Red Head with spots */}
          <div className="absolute top-6 left-1/2 transform -translate-x-1/2 w-20 h-20 bg-red-500 rounded-full border-4 border-black relative">
            {/* Face spots */}
            <div className="absolute top-2 left-2 w-2 h-2 bg-red-800 rounded-full"></div>
            <div className="absolute top-6 right-3 w-1 h-1 bg-red-800 rounded-full"></div>
            <div className="absolute bottom-8 left-4 w-1 h-1 bg-red-800 rounded-full"></div>
            
            {/* Energy lines */}
            <div className="absolute -left-3 top-2 w-4 h-1 bg-green-400"></div>
            <div className="absolute -left-2 top-5 w-3 h-1 bg-green-400"></div>
            <div className="absolute -right-3 top-2 w-4 h-1 bg-blue-400"></div>
            <div className="absolute -right-2 top-5 w-3 h-1 bg-blue-400"></div>
            
            {/* Black Sunglasses */}
            <div className="absolute top-4 left-1/2 transform -translate-x-1/2 w-12 h-6 bg-black rounded border-2 border-white">
              <div className="absolute top-1 left-1 w-2 h-1 bg-white"></div>
              <div className="absolute top-1 right-1 w-2 h-1 bg-white"></div>
            </div>
            
            {/* Big Blue Smile */}
            <div className="absolute bottom-2 left-1/2 transform -translate-x-1/2 w-12 h-6 bg-blue-500 rounded-full border-2 border-black">
              {/* White teeth */}
              <div className="absolute top-1 left-1/2 transform -translate-x-1/2 flex gap-px">
                <div className="w-2 h-3 bg-white"></div>
                <div className="w-2 h-3 bg-white"></div>
                <div className="w-2 h-3 bg-white"></div>
                <div className="w-2 h-3 bg-white"></div>
              </div>
            </div>
          </div>
          
          {/* Red Arms - Victory Pose */}
          <div className="absolute top-22 -left-4 w-5 h-12 bg-red-500 border-4 border-black rounded-full transform rotate-45">
            {/* Flexing bicep */}
            <div className="absolute top-2 -right-1 w-6 h-6 bg-red-500 rounded-full border-2 border-black"></div>
            {/* Fist */}
            <div className="absolute -bottom-2 -right-1 w-4 h-4 bg-red-500 rounded-full border-2 border-black"></div>
          </div>
          
          <div className="absolute top-24 -right-2 w-4 h-8 bg-red-500 border-4 border-black rounded-full transform rotate-12">
            {/* Hand on hip */}
            <div className="absolute -bottom-2 -left-1 w-4 h-4 bg-red-500 rounded-full border-2 border-black"></div>
          </div>
          
          {/* Pink Polka Dot Shirt */}
          <div className="absolute top-22 left-1/2 transform -translate-x-1/2 w-16 h-18 bg-pink-500 border-4 border-black rounded-lg">
            {/* Multiple polka dots */}
            <div className="absolute top-2 left-2 w-3 h-3 bg-black rounded-full"></div>
            <div className="absolute top-2 right-2 w-3 h-3 bg-black rounded-full"></div>
            <div className="absolute top-6 left-5 w-3 h-3 bg-black rounded-full"></div>
            <div className="absolute top-10 left-1 w-3 h-3 bg-black rounded-full"></div>
            <div className="absolute top-10 right-1 w-3 h-3 bg-black rounded-full"></div>
            <div className="absolute bottom-2 left-1/2 transform -translate-x-1/2 w-3 h-3 bg-black rounded-full"></div>
          </div>
          
          {/* Blue Striped Pants */}
          <div className="absolute bottom-12 left-1/2 transform -translate-x-1/2 w-18 h-16 bg-blue-500 border-4 border-black">
            {/* Wavy stripes */}
            <div className="absolute top-0 left-2 w-1 h-full bg-black transform rotate-2"></div>
            <div className="absolute top-0 left-4 w-1 h-full bg-black transform -rotate-1"></div>
            <div className="absolute top-0 left-6 w-1 h-full bg-black transform rotate-1"></div>
            <div className="absolute top-0 left-8 w-1 h-full bg-black transform -rotate-2"></div>
            <div className="absolute top-0 left-10 w-1 h-full bg-black transform rotate-1"></div>
            <div className="absolute top-0 right-2 w-1 h-full bg-black transform -rotate-1"></div>
          </div>
          
          {/* Black Boots */}
          <div className="absolute bottom-2 left-6 w-7 h-6 bg-black rounded border-2 border-black"></div>
          <div className="absolute bottom-2 right-6 w-7 h-6 bg-black rounded border-2 border-black"></div>
        </div>
        
        {/* Celebration Message */}
        <div className="mt-8 text-center animate-bounce">
          <div className="arteme-header text-2xl md:text-3xl inline-block" 
               style={{ 
                 backgroundColor: 'var(--color-primary-yellow)', 
                 color: 'var(--color-primary-black)',
                 border: '4px solid var(--color-primary-black)',
                 boxShadow: '6px 6px 0px var(--color-primary-black)',
                 padding: '12px 24px'
               }}>
            {currentMessage}
          </div>
        </div>
        
        {/* Celebration Effects */}
        <div className="absolute inset-0 pointer-events-none">
          {/* Confetti */}
          <div className="absolute top-10 left-10 w-4 h-4 bg-yellow-400 rounded-full animate-ping"></div>
          <div className="absolute top-20 right-15 w-3 h-3 bg-pink-500 animate-ping" style={{ animationDelay: '0.2s' }}></div>
          <div className="absolute bottom-20 left-20 w-5 h-5 bg-blue-400 rounded-full animate-ping" style={{ animationDelay: '0.4s' }}></div>
          <div className="absolute top-1/3 right-10 w-4 h-4 bg-green-400 animate-ping" style={{ animationDelay: '0.6s' }}></div>
          
          {/* Star bursts */}
          <div className="absolute top-16 left-1/4 w-6 h-6 star-shape bg-yellow-400 animate-spin"></div>
          <div className="absolute bottom-24 right-1/4 w-8 h-8 star-shape bg-pink-500 animate-spin" style={{ animationDelay: '0.3s' }}></div>
        </div>
      </div>
    </div>
  );
};

export default ZiggyBlaze;