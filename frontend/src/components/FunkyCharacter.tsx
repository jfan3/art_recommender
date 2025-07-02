import React, { useState, useEffect } from 'react';

interface FunkyCharacterProps {
  onInteraction?: (message: string) => void;
  isActive?: boolean;
}

const FunkyCharacter: React.FC<FunkyCharacterProps> = ({ 
  onInteraction, 
  isActive = false 
}) => {
  const [currentMood, setCurrentMood] = useState('default');
  const [isAnimating, setIsAnimating] = useState(false);

  // Character responses - fun and engaging conversation starters
  const characterResponses = [
    "Hey there, art lover! Ready to dive into the most amazing art discovery journey?",
    "I'm here to help you find art that'll make your heart sing! What's your vibe today?",
    "Welcome to the coolest art adventure! Tell me, what makes you feel most creative?",
    "Art is everywhere and I'm your guide to finding what speaks to YOU! Let's chat!",
    "Looking for some artistic inspiration? You've come to the right place, my friend!",
    "I've got my detective hat on and I'm ready to solve the mystery of your perfect art style!",
    "Hey art explorer! I'm pumped to help you discover amazing artworks. What's your mood?",
    "Welcome to your personal art universe! I'm here to make this journey super fun!",
    "Ready to find art that'll blow your mind? Let's start this creative conversation!",
    "I'm your friendly art companion! Tell me what kind of energy you're feeling today."
  ];

  // Animation moods with new funky movements
  const animations = {
    default: 'animate-character-bob',
    excited: 'animate-excited-jump',
    dancing: 'animate-dance',
    floating: 'animate-float',
    bouncing: 'animate-bounce-character',
    wiggling: 'animate-wiggle',
    swaying: 'animate-sway',
    walking: 'animate-funky-walk',
    sliding: 'animate-funky-slide',
    spinning: 'animate-funky-spin'
  };

  // Character interaction handler
  const handleCharacterClick = () => {
    if (onInteraction) {
      const randomResponse = characterResponses[Math.floor(Math.random() * characterResponses.length)];
      onInteraction(randomResponse);
      
      // Trigger celebration animation
      setIsAnimating(true);
      setCurrentMood('excited');
      
      setTimeout(() => {
        setCurrentMood('spinning');
      }, 800);
      
      setTimeout(() => {
        setCurrentMood('sliding');
      }, 1600);
      
      setTimeout(() => {
        setIsAnimating(false);
        setCurrentMood('default');
      }, 3000);
    }
  };

  // Ambient life animations with funky movements
  useEffect(() => {
    const interval = setInterval(() => {
      if (!isAnimating) {
        const randomMoods = ['floating', 'wiggling', 'bouncing', 'swaying', 'walking', 'sliding'];
        const randomMood = randomMoods[Math.floor(Math.random() * randomMoods.length)];
        setCurrentMood(randomMood);
        setTimeout(() => setCurrentMood('default'), 2500);
      }
    }, 3500);

    return () => clearInterval(interval);
  }, [isAnimating]);

  // Occasional spontaneous funky performance
  useEffect(() => {
    const performanceInterval = setInterval(() => {
      if (!isAnimating) {
        const performances = ['dancing', 'spinning', 'walking'];
        const randomPerformance = performances[Math.floor(Math.random() * performances.length)];
        setCurrentMood(randomPerformance);
        setTimeout(() => setCurrentMood('default'), 2000);
      }
    }, 10000);

    return () => clearInterval(performanceInterval);
  }, [isAnimating]);

  return (
    <div className="relative flex flex-col items-center">
      {/* Character Container with PNG Image */}
      <div 
        className={`relative cursor-pointer transition-all duration-500 hover:scale-110 ${animations[currentMood as keyof typeof animations]} ${isActive ? 'ring-4 ring-yellow-400 ring-opacity-60' : ''}`}
        onClick={handleCharacterClick}
        style={{
          width: '200px',
          height: '250px',
          filter: isActive ? 'brightness(1.1) contrast(1.1) drop-shadow(0 0 25px rgba(255, 202, 43, 0.6))' : 'brightness(1)',
        }}
      >
        
        {/* PNG Character Image - 标准图片加载方式 */}
        <img 
          src="/assets/new-character.png" 
          alt="ARTEME Funky Character"
          className="w-full h-full object-contain relative z-10"
          style={{
            filter: currentMood === 'excited' 
              ? 'brightness(1.3) contrast(1.4) saturate(1.8) hue-rotate(5deg) drop-shadow(0 0 15px rgba(230, 0, 38, 0.8))' 
              : 'brightness(1.1) contrast(1.2) saturate(1.6)',
            transition: 'filter 0.3s ease'
          }}
        />
        
        {/* Interactive Pulse Effect */}
        <div className="absolute inset-0 rounded-full opacity-0 hover:opacity-30 transition-opacity duration-300"
             style={{ 
               background: 'radial-gradient(circle, rgba(255, 202, 43, 0.3) 0%, transparent 70%)',
               animation: isActive ? 'pulse 2s infinite' : 'none'
             }}>
        </div>

        {/* Hover Interaction Hint */}
        <div className="absolute inset-0 flex items-end justify-center pb-6 opacity-0 hover:opacity-100 transition-opacity duration-300">
          <div className="bg-white/95 px-4 py-2 rounded-full text-sm font-bold text-black shadow-lg"
               style={{ border: '2px solid var(--color-primary-black)' }}>
            Click me to chat!
          </div>
        </div>
      </div>

      {/* Character Info */}
      <div className="mt-6 text-center">
        <div className="arteme-header text-base mb-3 inline-block">
          YOUR ART BUDDY
        </div>
        <div className="text-sm max-w-64" style={{ color: 'var(--color-primary-white)' }}>
          Click me to start chatting!
        </div>
      </div>

      {/* Animated floating elements when active */}
      {isAnimating && (
        <>
          {/* Floating geometric shapes - Egle style */}
          <div className="absolute -top-4 -left-4 w-6 h-6 rounded-full animate-bounce"
               style={{ backgroundColor: 'var(--color-primary-red)', animationDelay: '0s' }}></div>
          <div className="absolute -top-6 -right-2 w-4 h-4 animate-bounce star-shape"
               style={{ backgroundColor: 'var(--color-primary-yellow)', animationDelay: '0.2s' }}></div>
          <div className="absolute -bottom-4 -left-6 w-5 h-5 animate-bounce"
               style={{ 
                 backgroundColor: 'var(--color-accent-pink)', 
                 clipPath: 'polygon(50% 0%, 0% 100%, 100% 100%)',
                 animationDelay: '0.4s' 
               }}></div>
          <div className="absolute -bottom-6 -right-4 w-4 h-4 rounded-full animate-bounce"
               style={{ backgroundColor: 'var(--color-accent-skyblue)', animationDelay: '0.6s' }}></div>
          
          {/* Energy waves */}
          <div className="absolute inset-0 pointer-events-none">
            <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-80 h-80 border-4 border-yellow-400 rounded-full opacity-30 animate-ping"></div>
            <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-96 h-96 border-2 border-red-400 rounded-full opacity-20 animate-ping"
                 style={{ animationDelay: '0.5s' }}></div>
          </div>
        </>
      )}
    </div>
  );
};

export default FunkyCharacter;