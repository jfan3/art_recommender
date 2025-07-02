import React, { useState, useEffect } from 'react';

interface VilniusCharacterProps {
  onInteraction?: (message: string) => void;
  isActive?: boolean;
}

const VilniusCharacter: React.FC<VilniusCharacterProps> = ({ 
  onInteraction, 
  isActive = false 
}) => {
  const [currentExpression, setCurrentExpression] = useState('default');
  const [isAnimating, setIsAnimating] = useState(false);

  // Character expressions and animations
  const expressions = {
    default: 'animate-bounce',
    excited: 'animate-pulse',
    thinking: 'animate-ping',
    waving: 'animate-bounce'
  };

  // Fun character responses
  const characterResponses = [
    "Hey there! I'm the coolest character from Vilnius! Welcome to the art world! 🎭",
    "Want to know why Vilnius is the NEW COOL? It's because of amazing art like you're about to discover! 💫",
    "I've got stars in my pants and flowers in my heart! Perfect for finding your art style! ✨💕",
    "But seriously... where IS your artistic soul hiding? Let's find it together! 🤔",
    "Art is my passion! Tell me - do you love bold colors like my outfit? 🎨",
    "I'm like a walking art piece myself! Bold, colorful, and totally unique - just like the art you'll discover! 🌈",
    "The hearts beside me? Those are my art-loving friends! They're excited to help you find your perfect art match! 💕💕",
    "My tiger head represents fierce creativity! What kind of creative energy are you feeling today? 🐅",
    "See this yellow banner? It says Vilnius is cool, but I think YOU'RE pretty cool too! What art style speaks to you? 📯"
  ];

  // Trigger character interaction
  const handleCharacterClick = () => {
    if (onInteraction) {
      const randomResponse = characterResponses[Math.floor(Math.random() * characterResponses.length)];
      onInteraction(randomResponse);
      
      // Animate character
      setIsAnimating(true);
      setCurrentExpression('excited');
      
      setTimeout(() => {
        setIsAnimating(false);
        setCurrentExpression('default');
      }, 2000);
    }
  };

  // Auto-animate occasionally
  useEffect(() => {
    const interval = setInterval(() => {
      if (!isAnimating) {
        setCurrentExpression('waving');
        setTimeout(() => setCurrentExpression('default'), 1000);
      }
    }, 8000);

    return () => clearInterval(interval);
  }, [isAnimating]);

  return (
    <div className="relative flex flex-col items-center">
      {/* Character Image */}
      <div 
        className={`relative cursor-pointer transition-transform duration-300 hover:scale-105 ${expressions[currentExpression as keyof typeof expressions]} ${isActive ? 'ring-4 ring-yellow-400 ring-opacity-50' : ''}`}
        onClick={handleCharacterClick}
        style={{
          width: '200px',
          height: '280px',
          filter: isActive ? 'brightness(1.1) contrast(1.1)' : 'brightness(1)',
        }}
      >
        <img 
          src="/assets/vilnius-character.jpg" 
          alt="Vilnius Character"
          className="w-full h-full object-contain rounded-2xl shadow-lg"
          style={{
            border: '4px solid var(--color-primary-black)',
            boxShadow: '8px 8px 0px var(--color-primary-black)'
          }}
        />
        
        {/* Interactive hover overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent opacity-0 hover:opacity-100 transition-opacity duration-300 rounded-2xl flex items-end justify-center pb-4">
          <div className="bg-white/90 px-3 py-1 rounded-full text-xs font-bold text-black">
            Click me! 👋
          </div>
        </div>
      </div>

      {/* Character Name and Status */}
      <div className="mt-4 text-center">
        <div className="arteme-header text-sm mb-2 inline-block">
          VILNIUS
        </div>
        <div className="text-xs" style={{ color: 'var(--color-primary-white)' }}>
          {isActive ? '🎭 Ready to chat!' : '💭 Tap to activate'}
        </div>
      </div>

      {/* Floating elements for extra flair */}
      {isAnimating && (
        <>
          <div className="absolute -top-2 -left-2 text-2xl animate-bounce">⭐</div>
          <div className="absolute -top-2 -right-2 text-2xl animate-bounce delay-150">💫</div>
          <div className="absolute -bottom-2 -left-2 text-2xl animate-bounce delay-300">💕</div>
          <div className="absolute -bottom-2 -right-2 text-2xl animate-bounce delay-450">🎨</div>
        </>
      )}
    </div>
  );
};

export default VilniusCharacter;