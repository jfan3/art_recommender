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

  if (waiting) return <div>Waiting for recommendations from Hunter Agent...</div>;
  if (loading) return <div>Loading candidates...</div>;
  if (error) return <div style={{ color: 'red' }}>Error: {error}</div>;
  if (trainingComplete) return <div>Training complete! You have swiped right on 30 items. 🎉</div>;
  if (current >= candidates.length) return <div>No more candidates! 🎉</div>;

  const item = candidates[current];

  return (
    <div style={{ maxWidth: 400, margin: '0 auto', textAlign: 'center' }}>
      <div style={{ border: '1px solid #ccc', borderRadius: 12, padding: 24, marginBottom: 24 }}>
        {item.image_url && (
          <img src={item.image_url} alt={item.item_name || item.title} style={{ width: '100%', borderRadius: 8, marginBottom: 16 }} />
        )}
        <h2>{item.item_name || item.title}</h2>
      </div>
      <div>
        <button onClick={() => handleSwipe('swipe_left')} style={{ marginRight: 24, padding: '8px 24px', background: '#eee', borderRadius: 8, border: 'none' }}>Swipe Left</button>
        <button onClick={() => handleSwipe('swipe_right')} style={{ padding: '8px 24px', background: '#4caf50', color: 'white', borderRadius: 8, border: 'none' }}>Swipe Right</button>
      </div>
      <div style={{ marginTop: 16, color: '#888' }}>
        {current + 1} / {candidates.length}
      </div>
    </div>
  );
};

export default SwipeFlow; 