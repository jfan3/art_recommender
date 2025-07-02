import React, { useEffect, useState } from 'react';
import { toast } from 'react-hot-toast';

const HUNTER_API_URL = process.env.NEXT_PUBLIC_HUNTER_API_URL || 'http://localhost:8090';

interface Item {
  item_id: string;
  item_name: string;
  image_url: string;
  title?: string;
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

  // Poll for generation status
  useEffect(() => {
    let pollTimeout: NodeJS.Timeout;
    let cancelled = false;
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
      cancelled = true;
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
        if (!res.ok) throw new Error('Failed to fetch candidates');
        const data = await res.json();
        if (data.training_complete) {
          setTrainingComplete(true);
          return;
        }
        setCandidates(data.candidates || []);
        setCurrent(0);
      } catch (err: any) {
        setError(err.message || 'Error fetching candidates');
      } finally {
        setLoading(false);
      }
    };
    fetchCandidates();
  }, [userUuid, waiting]);

  // Step 3: Handle swipe
  const handleSwipe = async (direction: 'swipe_left' | 'swipe_right') => {
    if (!candidates[current]) return;
    const item = candidates[current];
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
      const data = await response.json();
      if (data.training_complete) {
        setTrainingComplete(true);
        toast.success('Training complete! You have swiped right on 30 items.');
        return;
      }
    } catch (err) {
      // Optionally handle error
    }
    setCurrent((prev) => prev + 1);
  };

  if (waiting) return (
    <div className="arteme-card text-center p-8">
      <div className="arteme-accent-bar w-24 mx-auto mb-6"></div>
      <h2 className="arteme-title text-3xl mb-4">Discovering Art</h2>
      <p className="text-lg mb-6 text-midnight-black/70">
        Finding the perfect recommendations for you
      </p>
      <div className="arteme-loading-dots justify-center">
        <div className="arteme-loading-dot"></div>
        <div className="arteme-loading-dot"></div>
        <div className="arteme-loading-dot"></div>
      </div>
    </div>
  );
  
  if (loading) return (
    <div className="arteme-card text-center p-8">
      <div className="arteme-accent-bar w-24 mx-auto mb-6"></div>
      <h2 className="arteme-title text-3xl mb-4">Loading Collection</h2>
      <div className="arteme-loading-dots justify-center">
        <div className="arteme-loading-dot"></div>
        <div className="arteme-loading-dot"></div>
        <div className="arteme-loading-dot"></div>
      </div>
    </div>
  );
  
  if (error) return (
    <div className="arteme-card text-center p-8">
      <div className="arteme-accent-bar w-24 mx-auto mb-6"></div>
      <h2 className="arteme-title text-3xl mb-4 text-cherry-red">Error</h2>
      <p className="text-lg text-cherry-red">{error}</p>
    </div>
  );
  
  if (trainingComplete) return (
    <div className="arteme-card text-center p-8">
      <div className="arteme-accent-bar w-32 mx-auto mb-6"></div>
      <h2 className="arteme-title text-4xl mb-4">Empire Complete!</h2>
      <div className="arteme-header inline-block">
        You've mastered your art taste!
      </div>
    </div>
  );
  
  if (current >= candidates.length) return (
    <div className="arteme-card text-center p-8">
      <div className="arteme-accent-bar w-32 mx-auto mb-6"></div>
      <h2 className="arteme-title text-4xl mb-4">All Done!</h2>
      <p className="text-xl">You've explored all recommendations</p>
    </div>
  );

  const item = candidates[current];

  return (
    <div className="flex flex-col items-center max-w-lg mx-auto">
      <div className="arteme-tarot-card p-8 mb-8 text-center relative w-full max-w-md">
        {item.image_url && (
          <img 
            src={item.image_url} 
            alt={item.item_name || item.title} 
            className="w-full mb-6 rounded-xl"
            style={{
              aspectRatio: '4/3',
              objectFit: 'cover'
            }}
          />
        )}
        
        <div className="mb-6">
          <h2 className="text-2xl font-bold arteme-title mb-2">
            {item.item_name || item.title}
          </h2>
          <div className="arteme-accent-bar w-16 mx-auto"></div>
        </div>
      </div>
      
      <div className="flex gap-6 mb-8">
        <button 
          onClick={() => handleSwipe('swipe_left')} 
          className="arteme-button arteme-button-secondary"
        >
          Skip
        </button>
        <button 
          onClick={() => handleSwipe('swipe_right')} 
          className="arteme-button arteme-button-primary"
        >
          Love It!
        </button>
      </div>
      
      <div className="text-center">
        <div className="arteme-card p-4 inline-block">
          <span className="font-bold text-lg text-midnight-black">
            {current + 1} / {candidates.length}
          </span>
        </div>
      </div>
    </div>
  );
};

export default SwipeFlow; 