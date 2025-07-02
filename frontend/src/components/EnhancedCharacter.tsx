import React, { useState, useEffect } from 'react';

interface EnhancedCharacterProps {
  onInteraction?: (message: string) => void;
  isActive?: boolean;
}

const EnhancedCharacter: React.FC<EnhancedCharacterProps> = ({ 
  onInteraction, 
  isActive = false 
}) => {
  const [currentCharacter] = useState(0); // Fixed to first character for elegance
  const [isAnimating, setIsAnimating] = useState(false);
  const [currentMood, setCurrentMood] = useState('default');

  // Character personas based on Egle's style
  const characters = [
    {
      name: "ARTEME",
      primaryColor: "#E60026",
      secondaryColor: "#FFCA2B", 
      personality: "energetic",
      description: "Your personal art discovery companion",
      responses: [
        "Welcome to the art universe! I'm here to help you discover your creative soul.",
        "Art is like energy - it flows through everything! What kind of energy are you feeling today?",
        "I've traveled through countless galleries and studios. Ready to find your artistic match?",
        "Your art journey is about to begin! Tell me what colors speak to your heart.",
        "Every masterpiece starts with curiosity. What's making you curious about art right now?",
        "I love helping people find their perfect art style! What kind of mood are you in today?",
        "Art speaks to everyone differently. Let's discover what speaks to you!",
        "Ready to explore the wonderful world of art together? I'm so excited to help!"
      ]
    },
    {
      name: "COSMIC",
      primaryColor: "#D3A4FF",
      secondaryColor: "#90D4F2",
      personality: "mystical", 
      description: "The celestial guide who reads artistic destinies",
      responses: [
        "The stars have aligned for your artistic awakening. What draws your spirit?",
        "I see great creative potential in your future. Let's unlock your artistic destiny.",
        "The universe speaks through art. What messages are you ready to receive?",
        "Your artistic path is written in the cosmos. Shall we read it together?",
        "Every soul has an artistic constellation. Help me map yours."
      ]
    },
    {
      name: "SCHOLAR", 
      primaryColor: "#0B1F3A",
      secondaryColor: "#F5E6DA",
      personality: "thoughtful",
      description: "The wise curator of knowledge and artistic history", 
      responses: [
        "Art history holds infinite treasures. What era calls to your imagination?",
        "Knowledge and creativity dance together beautifully. What style intrigues you?",
        "I've studied countless artistic movements. Ready to explore your preferences?",
        "Every artwork tells a story. What stories do you want to discover?",
        "The greatest artists learned from those before them. What inspires your learning?"
      ]
    }
  ];

  const currentChar = characters[currentCharacter];

  // Advanced animation states
  const animations = {
    default: 'animate-breathe',
    excited: 'animate-excited-jump', 
    thinking: 'animate-wiggle',
    floating: 'animate-float',
    dancing: 'animate-dance',
    glowing: 'animate-glow',
    bouncing: 'animate-bounce-character'
  };

  // Character interaction handler
  const handleCharacterClick = () => {
    if (onInteraction) {
      const randomResponse = currentChar.responses[Math.floor(Math.random() * currentChar.responses.length)];
      onInteraction(randomResponse);
      
      // Trigger animation sequence
      setIsAnimating(true);
      setCurrentMood('excited');
      
      setTimeout(() => {
        setCurrentMood('glowing');
      }, 500);
      
      setTimeout(() => {
        setIsAnimating(false);
        setCurrentMood('default');
      }, 2000);
    }
  };

  // Keep single character for welcome page elegance

  // Ambient animations - Make character more alive
  useEffect(() => {
    const interval = setInterval(() => {
      if (!isAnimating) {
        const randomMoods = ['floating', 'thinking', 'bouncing'];
        const randomMood = randomMoods[Math.floor(Math.random() * randomMoods.length)];
        setCurrentMood(randomMood);
        setTimeout(() => setCurrentMood('default'), 2500);
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [isAnimating]);

  // Eye blinking effect
  useEffect(() => {
    const blinkInterval = setInterval(() => {
      if (!isAnimating) {
        // Quick blink simulation by temporarily changing mood
        setCurrentMood('thinking');
        setTimeout(() => setCurrentMood('default'), 150);
      }
    }, 3000);

    return () => clearInterval(blinkInterval);
  }, [isAnimating]);

  return (
    <div className="relative flex flex-col items-center">
      {/* PNG-Style Character - No Frame */}
      <div 
        className={`relative cursor-pointer transition-all duration-500 hover:scale-110 ${animations[currentMood as keyof typeof animations]}`}
        onClick={handleCharacterClick}
        style={{
          width: '220px',
          height: '280px',
          filter: isActive ? 'brightness(1.2) contrast(1.1) drop-shadow(0 0 20px rgba(230, 0, 38, 0.4))' : 'brightness(1)',
        }}
      >
        {/* Character Head */}
        <div className="absolute top-0 left-1/2 transform -translate-x-1/2 w-24 h-24 rounded-full"
             style={{ 
               backgroundColor: currentChar.personality === 'mystical' ? '#FFB6C1' : 'var(--color-primary-white)', 
               border: '4px solid var(--color-primary-black)',
               zIndex: 10
             }}>
          {/* Hair/Top Details */}
          <div className="absolute -top-2 left-1/2 transform -translate-x-1/2 w-16 h-8 rounded-full"
               style={{ backgroundColor: currentChar.primaryColor, border: '3px solid var(--color-primary-black)' }}>
          </div>
          
          {/* Eyes with expressions */}
          <div className="absolute top-6 left-3 w-4 h-4 rounded-full bg-black flex items-center justify-center">
            <div className="w-2 h-2 rounded-full bg-white"></div>
          </div>
          <div className="absolute top-6 right-3 w-4 h-4 rounded-full bg-black flex items-center justify-center">
            <div className="w-2 h-2 rounded-full bg-white"></div>
          </div>
          
          {/* Nose */}
          <div className="absolute top-10 left-1/2 transform -translate-x-1/2 w-2 h-1 rounded-full"
               style={{ backgroundColor: currentChar.secondaryColor }}></div>
          
          {/* Mouth with expression */}
          <div className="absolute top-12 left-1/2 transform -translate-x-1/2 w-6 h-3 rounded-full"
               style={{ 
                 backgroundColor: currentMood === 'excited' ? '#FF6B6B' : currentChar.secondaryColor,
                 border: '2px solid var(--color-primary-black)'
               }}></div>
          
          {/* Cheeks */}
          <div className="absolute top-8 left-1 w-3 h-3 rounded-full"
               style={{ backgroundColor: currentChar.secondaryColor, opacity: 0.6 }}></div>
          <div className="absolute top-8 right-1 w-3 h-3 rounded-full"
               style={{ backgroundColor: currentChar.secondaryColor, opacity: 0.6 }}></div>
        </div>
        
        {/* Character Body */}
        <div className="absolute top-20 left-1/2 transform -translate-x-1/2 w-20 h-28"
             style={{
               backgroundColor: currentChar.primaryColor,
               border: '4px solid var(--color-primary-black)',
               borderRadius: '20px 20px 10px 10px',
               zIndex: 5
             }}>
          {/* Body Pattern */}
          <div className="absolute top-2 left-1/2 transform -translate-x-1/2 w-12 h-8 rounded-lg"
               style={{ backgroundColor: currentChar.secondaryColor, border: '2px solid var(--color-primary-black)' }}>
          </div>
        </div>
        
        {/* Character Arms with gestures */}
        <div className={`absolute top-24 left-2 w-6 h-16 rounded-full transform ${currentMood === 'excited' ? 'rotate-12' : currentMood === 'dancing' ? '-rotate-12' : 'rotate-6'} transition-transform duration-500`}
             style={{ backgroundColor: currentChar.personality === 'mystical' ? '#FFB6C1' : 'var(--color-primary-white)', border: '3px solid var(--color-primary-black)', zIndex: 3 }}>
          {/* Hand */}
          <div className="absolute -bottom-1 -right-1 w-4 h-4 rounded-full"
               style={{ backgroundColor: currentChar.personality === 'mystical' ? '#FFB6C1' : 'var(--color-primary-white)', border: '2px solid var(--color-primary-black)' }}>
          </div>
        </div>
        
        <div className={`absolute top-24 right-2 w-6 h-16 rounded-full transform ${currentMood === 'excited' ? '-rotate-12' : currentMood === 'dancing' ? 'rotate-12' : '-rotate-6'} transition-transform duration-500`}
             style={{ backgroundColor: currentChar.personality === 'mystical' ? '#FFB6C1' : 'var(--color-primary-white)', border: '3px solid var(--color-primary-black)', zIndex: 3 }}>
          {/* Hand */}
          <div className="absolute -bottom-1 -left-1 w-4 h-4 rounded-full"
               style={{ backgroundColor: currentChar.personality === 'mystical' ? '#FFB6C1' : 'var(--color-primary-white)', border: '2px solid var(--color-primary-black)' }}>
          </div>
        </div>
        
        {/* Character Legs */}
        <div className="absolute bottom-20 left-6 w-5 h-20 rounded-full"
             style={{ backgroundColor: currentChar.personality === 'mystical' ? '#FFB6C1' : 'var(--color-primary-white)', border: '3px solid var(--color-primary-black)', zIndex: 2 }}>
          {/* Foot */}
          <div className="absolute -bottom-2 -left-2 w-8 h-4 rounded-full"
               style={{ backgroundColor: 'var(--color-primary-black)' }}>
          </div>
        </div>
        
        <div className="absolute bottom-20 right-6 w-5 h-20 rounded-full"
             style={{ backgroundColor: currentChar.personality === 'mystical' ? '#FFB6C1' : 'var(--color-primary-white)', border: '3px solid var(--color-primary-black)', zIndex: 2 }}>
          {/* Foot */}
          <div className="absolute -bottom-2 -right-2 w-8 h-4 rounded-full"
               style={{ backgroundColor: 'var(--color-primary-black)' }}>
          </div>
        </div>
        
        {/* Character Special Elements based on personality */}
        {currentChar.personality === 'mystical' && (
          <>
            <div className="absolute top-2 left-8 w-3 h-3 star-shape"
                 style={{ backgroundColor: currentChar.secondaryColor }}></div>
            <div className="absolute top-8 right-8 w-4 h-4 star-shape"
                 style={{ backgroundColor: currentChar.primaryColor }}></div>
          </>
        )}
        
        {currentChar.personality === 'energetic' && (
          <>
            <div className="absolute top-12 left-0 w-4 h-4 rounded-full"
                 style={{ backgroundColor: currentChar.secondaryColor, border: '2px solid var(--color-primary-black)' }}></div>
            <div className="absolute top-32 right-0 w-3 h-3"
                 style={{ backgroundColor: currentChar.primaryColor, clipPath: 'polygon(50% 0%, 0% 100%, 100% 100%)' }}></div>
          </>
        )}

        {/* Interactive Hover Effect */}
        <div className="absolute inset-0 opacity-0 hover:opacity-100 transition-opacity duration-300 flex items-end justify-center pb-4">
          <div className="bg-white/95 px-4 py-2 rounded-full text-sm font-bold text-black">
            Chat with {currentChar.name}!
          </div>
        </div>
      </div>

      {/* Character Info Panel - Simplified */}
      <div className="mt-6 text-center max-w-48">
        <div className="arteme-header text-sm mb-2 inline-block" 
             style={{ backgroundColor: currentChar.primaryColor }}>
          {currentChar.name}
        </div>
        <div className="text-xs" style={{ color: 'var(--color-primary-white)' }}>
          {currentChar.description}
        </div>
      </div>

      {/* Floating Elements - No Emojis */}
      {isAnimating && (
        <>
          <div className="absolute -top-3 -left-3 w-4 h-4 rounded-full animate-bounce"
               style={{ backgroundColor: currentChar.primaryColor }}></div>
          <div className="absolute -top-3 -right-3 w-3 h-3 animate-bounce delay-150"
               style={{ backgroundColor: currentChar.secondaryColor, clipPath: 'polygon(50% 0%, 0% 100%, 100% 100%)' }}></div>
          <div className="absolute -bottom-3 -left-3 w-4 h-4 animate-bounce delay-300"
               style={{ backgroundColor: 'var(--color-accent-pink)', clipPath: 'polygon(20% 0%, 0% 20%, 30% 50%, 0% 80%, 20% 100%, 50% 70%, 80% 100%, 100% 80%, 70% 50%, 100% 20%, 80% 0%, 50% 30%)' }}></div>
          <div className="absolute -bottom-3 -right-3 w-3 h-3 rounded-full animate-bounce delay-450"
               style={{ backgroundColor: 'var(--color-accent-skyblue)' }}></div>
        </>
      )}
    </div>
  );
};

export default EnhancedCharacter;