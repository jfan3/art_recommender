import React, { useEffect, useState, useRef } from 'react';
import { toast } from 'react-hot-toast';
import ThreeMonthPlan from './three-month-plan';

const HUNTER_API_URL = process.env.NEXT_PUBLIC_HUNTER_API_URL || 'http://localhost:8000';

interface Item {
  item_id: string;
  item_name: string;
  image_url: string;
  title?: string;
  category?: string;
}

interface SwipeFlowProps {
  userUuid: string;
}

const POLL_INTERVAL = 1000; // 1 second

const SwipeFlow: React.FC<SwipeFlowProps> = ({ userUuid }) => {
  const [candidates, setCandidates] = useState<Item[]>([]);
  const [current, setCurrent] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [waiting, setWaiting] = useState(true);
  const [trainingComplete, setTrainingComplete] = useState(false);
  const [swipesComplete, setSwipesComplete] = useState(() => {
    // Check if swipes were already completed
    return localStorage.getItem('swipesComplete') === 'true';
  });
  
  // Swipe state
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const [swipeDirection, setSwipeDirection] = useState<'left' | 'right' | null>(null);
  const cardRef = useRef<HTMLDivElement>(null);

  // Poll for generation status
  useEffect(() => {
    // NO TEST USER SHORTCUTS - all users follow real workflow
    
    let pollTimeout: NodeJS.Timeout;
    const pollStatus = async () => {
      try {
        const res = await fetch(`${HUNTER_API_URL}/api/generation_status/${userUuid}`);
        if (!res.ok) throw new Error('Failed to check generation status');
        const data = await res.json();
        if (data.status === 'complete') {
          setWaiting(false);
        } else {
          setWaiting(true);
          pollTimeout = setTimeout(pollStatus, POLL_INTERVAL);
        }
      } catch (err: any) {
        setError(err.message || 'Error checking generation status');
      }
    };
    pollStatus();
    return () => {
      if (pollTimeout) clearTimeout(pollTimeout);
    };
  }, [userUuid]);

  // Fetch candidates only when status is complete
  useEffect(() => {
    if (waiting) return;
    const fetchCandidates = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(`${HUNTER_API_URL}/api/candidates/${userUuid}`);
        if (!res.ok) {
          // Handle specific error codes from consolidated API
          if (res.status === 503) {
            const errorData = await res.json().catch(() => ({}));
            throw new Error(errorData.detail || 'Backend services unavailable. Please ensure Supabase connection is active.');
          }
          
          // NO MOCK DATA - only real candidates
          
          const errorData = await res.json().catch(() => ({}));
          throw new Error(errorData.detail || `Failed to fetch candidates (${res.status})`);
        }
        const data = await res.json();
        if (data.training_complete) {
          setTrainingComplete(true);
          return;
        }
        setCandidates(data.candidates || []);
        setCurrent(0);
      } catch (err: any) {
        // NO MOCK DATA - show error for all cases
        setError(err.message || 'Error fetching real candidates. Please ensure your profile is complete and try again.');
      } finally {
        setLoading(false);
      }
    };
    fetchCandidates();
  }, [userUuid, waiting]);

  // Swipe gesture handlers
  const handleMouseDown = (e: React.MouseEvent) => {
    console.log('Mouse down detected');
    setIsDragging(true);
    setDragStart({ x: e.clientX, y: e.clientY });
    setDragOffset({ x: 0, y: 0 });
  };

  const handleTouchStart = (e: React.TouchEvent) => {
    setIsDragging(true);
    const touch = e.touches[0];
    setDragStart({ x: touch.clientX, y: touch.clientY });
    setDragOffset({ x: 0, y: 0 });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return;
    e.preventDefault();
    const offsetX = e.clientX - dragStart.x;
    const offsetY = e.clientY - dragStart.y;
    setDragOffset({ x: offsetX, y: offsetY });
    console.log('Dragging:', offsetX, offsetY);
    
    // Update swipe direction based on drag distance
    if (Math.abs(offsetX) > 50) {
      setSwipeDirection(offsetX > 0 ? 'right' : 'left');
      console.log('Swipe direction:', offsetX > 0 ? 'right' : 'left');
    } else {
      setSwipeDirection(null);
    }
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    if (!isDragging) return;
    const touch = e.touches[0];
    const offsetX = touch.clientX - dragStart.x;
    const offsetY = touch.clientY - dragStart.y;
    setDragOffset({ x: offsetX, y: offsetY });
    
    // Update swipe direction based on drag distance
    if (Math.abs(offsetX) > 50) {
      setSwipeDirection(offsetX > 0 ? 'right' : 'left');
    } else {
      setSwipeDirection(null);
    }
  };

  const handleMouseUp = () => {
    if (!isDragging) return;
    setIsDragging(false);
    
    // Execute swipe if threshold is met
    if (Math.abs(dragOffset.x) > 100) {
      const direction = dragOffset.x > 0 ? 'swipe_right' : 'swipe_left';
      handleSwipe(direction);
    }
    
    // Reset state
    setDragOffset({ x: 0, y: 0 });
    setSwipeDirection(null);
  };

  const handleTouchEnd = () => {
    if (!isDragging) return;
    setIsDragging(false);
    
    // Execute swipe if threshold is met
    if (Math.abs(dragOffset.x) > 100) {
      const direction = dragOffset.x > 0 ? 'swipe_right' : 'swipe_left';
      handleSwipe(direction);
    }
    
    // Reset state
    setDragOffset({ x: 0, y: 0 });
    setSwipeDirection(null);
  };

  const handleSwipe = async (direction: 'swipe_left' | 'swipe_right') => {
    if (!candidates[current]) return;
    const item = candidates[current];
    console.log(`Swiping ${direction} on item ${current + 1}/${candidates.length}`);
    try {
      const response = await fetch(`${HUNTER_API_URL}/api/swipe`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_uuid: userUuid,
          item_id: item.item_id,
          status: direction,
        }),
      });
      
      if (!response.ok) {
        // Handle specific error codes from consolidated API
        if (response.status === 503) {
          const errorData = await response.json().catch(() => ({}));
          toast.error(errorData.detail || 'Backend services unavailable. Please try again later.');
          return;
        }
        const errorData = await response.json().catch(() => ({}));
        toast.error(errorData.detail || `Error processing swipe (${response.status})`);
        return;
      }
      
      const data = await response.json();
      console.log('Swipe response:', data);
      
      if (data.training_complete) {
        setTrainingComplete(true);
        toast.success('Training complete! You have swiped right on 30 items.');
        return;
      }
      if (data.swipes_complete) {
        console.log('Setting swipesComplete to true');
        toast.success(`Preference learning complete! Generating your personalized 3-month art journey...`);
        setSwipesComplete(true);
        localStorage.setItem('swipesComplete', 'true');
        return;
      }
    } catch (err: any) {
      console.error('Error swiping:', err);
      toast.error(err.message || 'Error processing swipe. Please try again.');
      return;
    }
    // Only increment if we haven't completed swipes
    setCurrent((prev) => prev + 1);
  };

  // Add global mouse event listeners for better drag handling
  React.useEffect(() => {
    const handleGlobalMouseMove = (e: MouseEvent) => {
      if (!isDragging) return;
      e.preventDefault();
      const offsetX = e.clientX - dragStart.x;
      const offsetY = e.clientY - dragStart.y;
      setDragOffset({ x: offsetX, y: offsetY });
      
      if (Math.abs(offsetX) > 50) {
        setSwipeDirection(offsetX > 0 ? 'right' : 'left');
      } else {
        setSwipeDirection(null);
      }
    };

    const handleGlobalMouseUp = () => {
      if (!isDragging) return;
      setIsDragging(false);
      
      if (Math.abs(dragOffset.x) > 100) {
        const direction = dragOffset.x > 0 ? 'swipe_right' : 'swipe_left';
        handleSwipe(direction);
      }
      
      setDragOffset({ x: 0, y: 0 });
      setSwipeDirection(null);
    };

    if (isDragging) {
      document.addEventListener('mousemove', handleGlobalMouseMove);
      document.addEventListener('mouseup', handleGlobalMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleGlobalMouseMove);
      document.removeEventListener('mouseup', handleGlobalMouseUp);
    };
  }, [isDragging, dragStart, dragOffset]);

  if (waiting) return (
    <div className="text-center" style={{ maxWidth: '600px', margin: '0 auto', paddingTop: '10px', paddingBottom: '24px' }}>
      <h2 className="arteme-title text-4xl mb-4" style={{ color: 'var(--color-primary-white)' }}>Discovering Art</h2>
      <p className="text-xl" style={{ color: 'var(--color-primary-white)', marginBottom: '100px' }}>
        Finding the personalized recommendations for you
      </p>
      
      {/* 3D Cube Animation */}
      <div className="cube-container mb-8" style={{ 
        perspective: '1200px', 
        display: 'flex', 
        justifyContent: 'center',
        height: '180px'
      }}>
        <div className="cube" style={{
          width: '120px',
          height: '120px',
          position: 'relative',
          transformStyle: 'preserve-3d',
          animation: 'rotateCube 3s infinite linear'
        }}>
          <div className="cube-face cube-front" style={{
            position: 'absolute',
            width: '120px',
            height: '120px',
            background: 'linear-gradient(135deg, #E60026, #FF6B6B)',
            border: '3px solid #000',
            transform: 'rotateY(0deg) translateZ(60px)'
          }}></div>
          <div className="cube-face cube-back" style={{
            position: 'absolute',
            width: '120px',
            height: '120px',
            background: 'linear-gradient(135deg, #FFCA2B, #FFE066)',
            border: '3px solid #000',
            transform: 'rotateY(180deg) translateZ(60px)'
          }}></div>
          <div className="cube-face cube-right" style={{
            position: 'absolute',
            width: '120px',
            height: '120px',
            background: 'linear-gradient(135deg, #90D4F2, #B3E5FC)',
            border: '3px solid #000',
            transform: 'rotateY(90deg) translateZ(60px)'
          }}></div>
          <div className="cube-face cube-left" style={{
            position: 'absolute',
            width: '120px',
            height: '120px',
            background: 'linear-gradient(135deg, #D3A4FF, #E1BEE7)',
            border: '3px solid #000',
            transform: 'rotateY(-90deg) translateZ(60px)'
          }}></div>
          <div className="cube-face cube-top" style={{
            position: 'absolute',
            width: '120px',
            height: '120px',
            background: 'linear-gradient(135deg, #FFB6C1, #FFCCCB)',
            border: '3px solid #000',
            transform: 'rotateX(90deg) translateZ(60px)'
          }}></div>
          <div className="cube-face cube-bottom" style={{
            position: 'absolute',
            width: '120px',
            height: '120px',
            background: 'linear-gradient(135deg, #FFA07A, #FFB07A)',
            border: '3px solid #000',
            transform: 'rotateX(-90deg) translateZ(60px)'
          }}></div>
        </div>
      </div>
      
      <style jsx>{`
        @keyframes rotateCube {
          0% { transform: rotateX(0deg) rotateY(0deg) rotateZ(0deg); }
          33% { transform: rotateX(120deg) rotateY(120deg) rotateZ(0deg); }
          66% { transform: rotateX(240deg) rotateY(240deg) rotateZ(120deg); }
          100% { transform: rotateX(360deg) rotateY(360deg) rotateZ(360deg); }
        }
      `}</style>
    </div>
  );
  
  if (loading) return (
    <div className="text-center" style={{ maxWidth: '600px', margin: '0 auto', paddingTop: '10px', paddingBottom: '24px' }}>
      <h2 className="arteme-title text-4xl mb-4" style={{ color: 'var(--color-primary-white)' }}>Loading Collection</h2>
      <p className="text-xl" style={{ color: 'var(--color-primary-white)', marginBottom: '100px' }}>
        Preparing your art discoveries
      </p>
      
      {/* 3D Cube Animation */}
      <div className="cube-container mb-8" style={{ 
        perspective: '1200px', 
        display: 'flex', 
        justifyContent: 'center',
        height: '180px'
      }}>
        <div className="cube" style={{
          width: '120px',
          height: '120px',
          position: 'relative',
          transformStyle: 'preserve-3d',
          animation: 'rotateCube 3s infinite linear'
        }}>
          <div className="cube-face cube-front" style={{
            position: 'absolute',
            width: '120px',
            height: '120px',
            background: 'linear-gradient(135deg, #E60026, #FF6B6B)',
            border: '3px solid #000',
            transform: 'rotateY(0deg) translateZ(60px)'
          }}></div>
          <div className="cube-face cube-back" style={{
            position: 'absolute',
            width: '120px',
            height: '120px',
            background: 'linear-gradient(135deg, #FFCA2B, #FFE066)',
            border: '3px solid #000',
            transform: 'rotateY(180deg) translateZ(60px)'
          }}></div>
          <div className="cube-face cube-right" style={{
            position: 'absolute',
            width: '120px',
            height: '120px',
            background: 'linear-gradient(135deg, #90D4F2, #B3E5FC)',
            border: '3px solid #000',
            transform: 'rotateY(90deg) translateZ(60px)'
          }}></div>
          <div className="cube-face cube-left" style={{
            position: 'absolute',
            width: '120px',
            height: '120px',
            background: 'linear-gradient(135deg, #D3A4FF, #E1BEE7)',
            border: '3px solid #000',
            transform: 'rotateY(-90deg) translateZ(60px)'
          }}></div>
          <div className="cube-face cube-top" style={{
            position: 'absolute',
            width: '120px',
            height: '120px',
            background: 'linear-gradient(135deg, #FFB6C1, #FFCCCB)',
            border: '3px solid #000',
            transform: 'rotateX(90deg) translateZ(60px)'
          }}></div>
          <div className="cube-face cube-bottom" style={{
            position: 'absolute',
            width: '120px',
            height: '120px',
            background: 'linear-gradient(135deg, #FFA07A, #FFB07A)',
            border: '3px solid #000',
            transform: 'rotateX(-90deg) translateZ(60px)'
          }}></div>
        </div>
      </div>
      
      <style jsx>{`
        @keyframes rotateCube {
          0% { transform: rotateX(0deg) rotateY(0deg) rotateZ(0deg); }
          33% { transform: rotateX(120deg) rotateY(120deg) rotateZ(0deg); }
          66% { transform: rotateX(240deg) rotateY(240deg) rotateZ(120deg); }
          100% { transform: rotateX(360deg) rotateY(360deg) rotateZ(360deg); }
        }
      `}</style>
    </div>
  );
  
  if (error) return (
    <div className="arteme-card text-center p-8">
      <div className="arteme-accent-bar w-24 mx-auto mb-6"></div>
      <h2 className="arteme-title text-3xl mb-4 text-cherry-red">Error</h2>
      <p className="text-lg text-cherry-red">{error}</p>
    </div>
  );
  
  // Check swipesComplete first - this takes priority over other states
  if (swipesComplete) {
    return <ThreeMonthPlan userUuid={userUuid} />;
  }
  
  if (trainingComplete) return (
    <div className="arteme-card text-center p-8">
      <div className="arteme-accent-bar w-32 mx-auto mb-6"></div>
      <h2 className="arteme-title text-4xl mb-4">Empire Complete!</h2>
      <div className="arteme-header inline-block">
        You've mastered your art taste!
      </div>
    </div>
  );
  
  // Only show "All Done" if we haven't completed swipes yet
  if (current >= candidates.length && !swipesComplete) return (
    <div className="arteme-card text-center p-8">
      <div className="arteme-accent-bar w-32 mx-auto mb-6"></div>
      <h2 className="arteme-title text-4xl mb-4">All Done!</h2>
      <p className="text-xl">You've explored all recommendations</p>
    </div>
  );

  const item = candidates[current];

  // Calculate card transform based on drag
  const getCardTransform = () => {
    if (!isDragging && dragOffset.x === 0) return 'translate(0px, 0px) rotate(0deg)';
    
    const rotation = dragOffset.x * 0.1; // Subtle rotation effect
    const opacity = Math.max(0.7, 1 - Math.abs(dragOffset.x) / 300);
    
    return `translate(${dragOffset.x}px, ${dragOffset.y * 0.1}px) rotate(${rotation}deg)`;
  };

  const getCardOpacity = () => {
    if (!isDragging && dragOffset.x === 0) return 1;
    return Math.max(0.7, 1 - Math.abs(dragOffset.x) / 300);
  };

  return (
    <div className="h-screen relative overflow-hidden flex flex-col" style={{ background: 'var(--color-primary-red)' }}>

      {/* Swipe Indicators */}
      {swipeDirection && (
        <div className={`absolute top-1/2 ${swipeDirection === 'left' ? 'left-8' : 'right-8'} 
                        transform -translate-y-1/2 z-20 pointer-events-none`}>
          <div className={`px-6 py-3 rounded-full text-white font-bold text-xl
                          ${swipeDirection === 'left' 
                            ? 'bg-red-500 bg-opacity-80' 
                            : 'bg-green-500 bg-opacity-80'}`}>
            {swipeDirection === 'left' ? 'SKIP' : 'LOVE'}
          </div>
        </div>
      )}

      {/* Main Content Container - 60px from top */}
      <div className="flex flex-col items-center p-4" style={{ height: '100vh', paddingTop: '60px' }}>
        {/* Card and Category Container */}
        <div className="flex items-center gap-4" style={{ marginBottom: '30px' }}>
          {/* Swipeable Card - Positioned higher */}
          <div 
            ref={cardRef}
            className="relative cursor-grab active:cursor-grabbing select-none"
            style={{
              width: '45vw', // Smaller size - 45% of screen width
              maxWidth: '380px', // Slightly reduced maximum width
              minWidth: '280px', // Minimum width limit
              height: '50vh', // Reduced height to leave space for buttons
              maxHeight: '350px', // Reduced maximum height
              transform: getCardTransform(),
              opacity: getCardOpacity(),
              transition: isDragging ? 'none' : 'all 0.3s ease-out'
            }}
            onMouseDown={handleMouseDown}
            onTouchStart={handleTouchStart}
            onTouchMove={handleTouchMove}
            onTouchEnd={handleTouchEnd}
          >
            <div className="arteme-card w-full h-full p-4 flex flex-col justify-between shadow-2xl">
              {/* Image - Fully filled card style */}
              {item.image_url && (
                <div className="flex-1 flex items-center justify-center overflow-hidden rounded-lg mb-3">
                  <img 
                    src={item.image_url} 
                    alt={item.item_name || item.title} 
                    className="w-full h-full object-cover"
                    style={{
                      minWidth: '100%',
                      minHeight: '100%'
                    }}
                    draggable={false}
                  />
                </div>
              )}
              
              {/* Title */}
              <div className="text-center">
                <h2 className="text-lg font-bold arteme-title mb-2 line-clamp-2">
                  {item.item_name || item.title}
                </h2>
                <div className="arteme-accent-bar w-12 mx-auto"></div>
              </div>
            </div>
          </div>

          {/* Category Button - Positioned beside the card */}
          {item.category && (
            <div className="flex-shrink-0">
              <button 
                className="bg-yellow-400 hover:bg-yellow-500 text-black px-3 py-6 rounded-full font-bold text-sm shadow-lg border-2 border-black"
                onClick={() => {
                  toast.success(`Category: ${item.category}`);
                }}
                style={{ writingMode: 'vertical-rl', textOrientation: 'upright' }}
              >
                {item.category}
              </button>
            </div>
          )}
        </div>

        {/* Bottom section with buttons only - 20px from artwork */}
        <div className="flex flex-col items-center">
          {/* Action Buttons Row - Positioned under the image */}
          <div className="flex gap-8 items-center">
            <button 
              onClick={() => handleSwipe('swipe_left')} 
              className="arteme-button bg-yellow-400 hover:bg-yellow-500 text-black px-8 py-3 rounded-full font-bold text-base shadow-lg border-2 border-black"
            >
              SKIP
            </button>
            
            <button 
              onClick={() => handleSwipe('swipe_right')} 
              className="arteme-button bg-green-500 hover:bg-green-600 text-white px-8 py-3 rounded-full font-bold text-base shadow-lg"
            >
              LOVE IT!
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SwipeFlow;