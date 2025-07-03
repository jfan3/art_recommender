'use client';

import { useState, useEffect } from 'react';
import { toast } from 'react-hot-toast';

const HUNTER_API_URL = process.env.NEXT_PUBLIC_HUNTER_API_URL || 'http://localhost:8090';

interface PlanItem {
  title: string;
  type: string;
  description: string;
  source_url: string;
  image_url: string;
  score: number;
  category: string;
  creator: string;
}

interface WeeklyPlan {
  [key: string]: PlanItem[];
}

interface PlanStatistics {
  total_items: number;
  total_time_hours: number;
  weeks: number;
  avg_hours_per_week: number;
}

interface ThreeMonthPlanProps {
  userUuid: string;
}

const ThreeMonthPlan: React.FC<ThreeMonthPlanProps> = ({ userUuid }) => {
  const [weeklyPlan, setWeeklyPlan] = useState<WeeklyPlan | null>(null);
  const [statistics, setStatistics] = useState<PlanStatistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchPlan = async () => {
      try {
        const response = await fetch(`${HUNTER_API_URL}/api/user_plan/${userUuid}`);
        const data = await response.json();
        
        if (data.plan_exists) {
          setWeeklyPlan(data.weekly_plan);
          setStatistics(data.statistics);
        } else {
          setError(data.message || 'No plan available');
        }
      } catch (err) {
        setError('Failed to load your plan');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchPlan();
  }, [userUuid]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: 'var(--color-primary-red)' }}>
        <div className="text-center">
          <h2 className="text-2xl font-bold text-white mb-4">Loading Your 3-Month Art Journey...</h2>
          <div className="arteme-loading-dots">
            <div className="arteme-loading-dot"></div>
            <div className="arteme-loading-dot"></div>
            <div className="arteme-loading-dot"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: 'var(--color-primary-red)' }}>
        <div className="arteme-card text-center p-8">
          <h2 className="arteme-title text-2xl mb-4">Plan Not Ready</h2>
          <p className="text-lg mb-4">{error}</p>
          <button 
            onClick={() => window.location.reload()}
            className="arteme-button bg-blue-500 hover:bg-blue-600 text-white px-6 py-2 rounded-lg"
          >
            Refresh
          </button>
        </div>
      </div>
    );
  }

  if (!weeklyPlan || !statistics) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: 'var(--color-primary-red)' }}>
        <div className="arteme-card text-center p-8">
          <h2 className="arteme-title text-2xl mb-4">No Plan Available</h2>
          <p className="text-lg">Complete your preference learning to generate a personalized plan.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-4" style={{ background: 'var(--color-primary-red)' }}>
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="text-4xl lg:text-5xl arteme-title mb-4" style={{ color: 'var(--color-primary-white)' }}>
          Your 3-Month Art Journey
        </h1>
        <div className="arteme-header mb-4 text-sm lg:text-base inline-block" style={{ 
          backgroundColor: 'var(--color-primary-yellow)', 
          color: 'var(--color-primary-black)',
          border: '3px solid var(--color-primary-black)',
          boxShadow: '4px 4px 0px var(--color-primary-black)',
          padding: '8px 16px'
        }}>
          Personalized Recommendations
        </div>
      </div>

      {/* Statistics */}
      <div className="max-w-4xl mx-auto mb-8">
        <div className="arteme-card p-6 mb-6">
          <h2 className="arteme-title text-2xl mb-4">Plan Overview</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-3xl font-bold arteme-title">{statistics.total_items}</div>
              <div className="text-sm">Items</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold arteme-title">{statistics.weeks}</div>
              <div className="text-sm">Weeks</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold arteme-title">{statistics.total_time_hours}h</div>
              <div className="text-sm">Total Time</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold arteme-title">{Math.round(statistics.avg_hours_per_week)}h</div>
              <div className="text-sm">Per Week</div>
            </div>
          </div>
        </div>
      </div>

      {/* Weekly Plan */}
      <div className="max-w-6xl mx-auto">
        <div className="grid gap-6">
          {Object.entries(weeklyPlan).map(([week, items]) => (
            <div key={week} className="arteme-card p-6">
              <h3 className="arteme-title text-xl mb-4">{week}</h3>
              {items.length === 0 ? (
                <p className="text-gray-600">No items planned for this week</p>
              ) : (
                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {items.map((item, index) => (
                    <div key={index} className="border rounded-lg p-4 bg-white">
                      <div className="flex justify-between items-start mb-2">
                        <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded uppercase font-semibold">
                          {item.type}
                        </span>
                        <span className="text-xs text-gray-500">
                          Score: {item.score.toFixed(2)}
                        </span>
                      </div>
                      
                      <h4 className="font-bold text-lg mb-2 line-clamp-2">{item.title}</h4>
                      
                      {item.creator && (
                        <p className="text-sm text-gray-600 mb-2">by {item.creator}</p>
                      )}
                      
                      {item.description && (
                        <p className="text-sm text-gray-700 mb-3 line-clamp-3">{item.description}</p>
                      )}
                      
                      <div className="flex justify-between items-center">
                        {item.source_url && item.source_url !== "N/A (manual entry)" && (
                          <a 
                            href={item.source_url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:text-blue-800 text-sm underline"
                          >
                            View Source
                          </a>
                        )}
                        <span className="text-xs text-gray-500">
                          {item.category}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Footer */}
      <div className="text-center mt-12 mb-8">
        <div className="arteme-card p-6 max-w-2xl mx-auto">
          <h3 className="arteme-title text-xl mb-3">Ready to Start Your Journey?</h3>
          <p className="text-gray-700 mb-4">
            Your personalized art journey has been carefully curated based on your preferences. 
            Each week offers a balanced mix of different art forms to enrich your cultural experience.
          </p>
          <button 
            onClick={() => toast.success('Your art journey begins now! 🎨')}
            className="arteme-button bg-green-500 hover:bg-green-600 text-white px-8 py-3 rounded-full font-bold"
          >
            Begin Journey
          </button>
        </div>
      </div>
    </div>
  );
};

export default ThreeMonthPlan;