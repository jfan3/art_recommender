'use client';

import { useState, useEffect } from 'react';
import { toast } from 'react-hot-toast';

const HUNTER_API_URL = process.env.NEXT_PUBLIC_HUNTER_API_URL || 'http://localhost:8000';

interface PlanItem {
  id?: string;
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
  const [viewDuration, setViewDuration] = useState<1 | 2 | 3>(3); // Duration to display
  const [viewIntensity, setViewIntensity] = useState<'chill' | 'medium' | 'intense'>('medium'); // Intensity level

  useEffect(() => {
    const fetchPlan = async () => {
      try {
        console.log(`Fetching plan for ${userUuid} with duration=${viewDuration}, intensity=${viewIntensity}`);
        const response = await fetch(`${HUNTER_API_URL}/api/plan/${userUuid}?duration=${viewDuration}&intensity=${viewIntensity}`);
        const data = await response.json();
        
        console.log('Plan API response:', data);
        
        if (data.success && data.weekly_plan && Object.keys(data.weekly_plan).length > 0) {
          console.log('Weekly plan data:', data.weekly_plan);
          setWeeklyPlan(data.weekly_plan);
          setStatistics({
            total_items: data.total_items || 0,
            total_time_hours: data.total_time_hours || 0,
            weeks: data.total_weeks || 0,
            avg_hours_per_week: data.avg_hours_per_week || 0
          });
        } else {
          console.log('No plan exists:', data.message);
          // Check if user has completed swiping and try to generate plan
          try {
            console.log('Checking if we can generate a plan for user:', userUuid);
            const swipeResponse = await fetch(`${HUNTER_API_URL}/api/swipe`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                user_uuid: userUuid,
                item_id: 'check_status',
                status: 'check_status'
              })
            });
            
            if (swipeResponse.ok) {
              const swipeData = await swipeResponse.json();
              console.log('Swipe status response:', swipeData);
              
              if (swipeData.swipes_complete) {
                console.log('User has completed swiping, plan should exist. Refreshing...');
                setTimeout(() => {
                  window.location.reload();
                }, 2000);
                setError('Plan is being generated. Please wait...');
              } else {
                setError('Please complete your preference learning by swiping on more items.');
              }
            } else {
              setError(data.message || 'No plan available. Please complete your preference learning first.');
            }
          } catch (genErr) {
            console.error('Error checking status:', genErr);
            setError(data.message || 'No plan available. Please complete your preference learning first.');
          }
        }
      } catch (err) {
        console.error('Error fetching plan:', err);
        setError('Failed to load your plan');
      } finally {
        setLoading(false);
      }
    };

    fetchPlan();
  }, [userUuid, viewDuration, viewIntensity]);

  // Filter weekly plan based on selected duration
  const getFilteredPlan = () => {
    if (!weeklyPlan) {
      console.log('No weekly plan data available');
      return null;
    }
    
    console.log('Raw weekly plan:', weeklyPlan);
    const maxWeeks = viewDuration * 4; // 4 weeks per month
    const filteredPlan: WeeklyPlan = {};
    
    Object.entries(weeklyPlan)
      .slice(0, maxWeeks)
      .forEach(([week, items]) => {
        filteredPlan[week] = items;
      });
    
    console.log('Filtered plan:', filteredPlan);
    return filteredPlan;
  };

  // Generate month headers based on selected duration
  const getMonthHeaders = () => {
    const months = [];
    for (let i = 1; i <= viewDuration; i++) {
      months.push(i);
    }
    return months;
  };

  const filteredPlan = getFilteredPlan();

  const displayPlan = filteredPlan;

  // Calculate statistics based on filtered plan and intensity
  const calculateDisplayStatistics = () => {
    if (!displayPlan) {
      return {
        total_items: 0,
        total_time_hours: 0,
        weeks: 0,
        avg_hours_per_week: 0
      };
    }

    const weeks = viewDuration * 4;
    let total_items = 0;
    let total_time_hours = 0;

    // Intensity multipliers
    const intensityMultipliers = {
      'chill': 0.7,    // 30% less time
      'medium': 1.0,   // Normal time
      'intense': 1.4   // 40% more time
    };

    const multiplier = intensityMultipliers[viewIntensity] || 1.0;

    Object.entries(displayPlan).forEach(([, items]) => {
      total_items += items.length;
      
      items.forEach(item => {
        const item_type = item.type?.toLowerCase() || 'art';
        let base_time = 2.0; // Default 2 hours
        
        // Estimate time based on content type
        if (item_type.includes('art') || item_type.includes('poetry')) {
          base_time = 1.0;
        } else if (item_type.includes('book')) {
          base_time = 8.0;
        } else if (item_type.includes('movie') || item_type.includes('musical')) {
          base_time = 2.5;
        } else if (item_type.includes('music') || item_type.includes('podcast')) {
          base_time = 1.5;
        }
        
        total_time_hours += base_time * multiplier;
      });
    });

    return {
      total_items,
      total_time_hours: Math.round(total_time_hours),
      weeks,
      avg_hours_per_week: Math.round((total_time_hours / weeks) * 10) / 10
    };
  };

  // Use calculated statistics based on current view settings
  const displayStatistics = calculateDisplayStatistics();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: 'var(--color-primary-red)' }}>
        <div className="text-center">
          <h2 className="text-2xl font-bold text-white mb-4">Loading Your {viewDuration}-Month Art Journey...</h2>
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

  const handleGeneratePlan = async () => {
    try {
      console.log('Manually triggering plan generation for user:', userUuid);
      const response = await fetch(`${HUNTER_API_URL}/api/generate_candidates/${userUuid}`, {
        method: 'POST'
      });
      
      if (response.ok) {
        console.log('Plan generation triggered successfully');
        setError('Generating your personalized plan... Please wait.');
        setTimeout(() => {
          window.location.reload();
        }, 5000);
      } else {
        setError('Unable to generate plan. Please ensure you have completed swiping.');
      }
    } catch (err) {
      console.error('Error generating plan:', err);
      setError('Error generating plan. Please try again.');
    }
  };

  if (!weeklyPlan && !statistics) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: 'var(--color-primary-red)' }}>
        <div className="arteme-card text-center p-8">
          <h2 className="arteme-title text-2xl mb-4">No Plan Available</h2>
          <p className="text-lg mb-6">Complete your preference learning to generate a personalized plan.</p>
          <button 
            onClick={handleGeneratePlan}
            className="arteme-button bg-blue-500 hover:bg-blue-600 text-white px-6 py-3 rounded-lg font-bold"
          >
            Generate My Plan
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-4" style={{ background: 'var(--color-primary-red)' }}>
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="text-4xl lg:text-5xl arteme-title mb-4" style={{ color: 'var(--color-primary-white)' }}>
          Your {viewDuration}-Month Art Journey
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

      {/* Plan Controls */}
      <div className="max-w-5xl mx-auto mb-8 px-4 mx-8">
        <div className="bg-white rounded-2xl shadow-xl p-6">
          {/* Section Header */}
          <div className="text-center mb-6">
            <h2 className="arteme-title text-xl lg:text-2xl mb-2" style={{ color: 'var(--color-primary-black)' }}>
              Customize Your Journey
            </h2>
            <div className="w-16 h-1 bg-gradient-to-r from-purple-500 to-blue-500 rounded-full mx-auto"></div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-8">
            {/* Duration Selection */}
            <div className="space-y-4">
              <div className="text-center lg:text-left">
                <h3 className="arteme-title text-lg mb-1" style={{ color: 'var(--color-primary-black)' }}>
                  Journey Duration
                </h3>
                <p className="text-gray-600 text-sm">
                  Choose how long you want your art journey to last
                </p>
              </div>
              
              <div className="flex lg:flex-col gap-2 lg:gap-3">
                {[1, 2, 3].map((duration) => (
                  <button
                    key={duration}
                    type="button"
                    onClick={() => setViewDuration(duration as 1 | 2 | 3)}
                    className={`arteme-button flex-1 lg:w-full py-3 px-4 font-bold text-base transition-all duration-300 transform hover:scale-105 ${
                      viewDuration === duration
                        ? 'bg-purple-600 text-white border-3 border-black shadow-lg'
                        : 'bg-white text-purple-600 border-3 border-purple-600 hover:bg-purple-50'
                    }`}
                    style={{
                      boxShadow: viewDuration === duration 
                        ? '4px 4px 0px var(--color-primary-black)' 
                        : '3px 3px 0px var(--color-purple-600)'
                    }}
                  >
                    {duration} Month{duration > 1 ? 's' : ''}
                  </button>
                ))}
              </div>
            </div>
            
            {/* Intensity Selection */}
            <div className="space-y-4">
              <div className="text-center lg:text-left">
                <h3 className="arteme-title text-lg mb-1" style={{ color: 'var(--color-primary-black)' }}>
                  Engagement Level
                </h3>
                <p className="text-gray-600 text-sm">
                  Select your preferred intensity and time commitment
                </p>
              </div>
              
              <div className="flex lg:flex-col gap-2 lg:gap-3">
                <button
                  type="button"
                  onClick={() => setViewIntensity('chill')}
                  className={`arteme-button flex-1 lg:w-full py-3 px-4 font-bold text-base transition-all duration-300 transform hover:scale-105 ${
                    viewIntensity === 'chill'
                      ? 'bg-green-500 text-white border-3 border-black shadow-lg'
                      : 'bg-white text-green-600 border-3 border-green-500 hover:bg-green-50'
                  }`}
                  style={{
                    boxShadow: viewIntensity === 'chill' 
                      ? '4px 4px 0px var(--color-primary-black)' 
                      : '3px 3px 0px #10b981'
                  }}
                >
                  Relaxed
                </button>
                
                <button
                  type="button"
                  onClick={() => setViewIntensity('medium')}
                  className={`arteme-button flex-1 lg:w-full py-3 px-4 font-bold text-base transition-all duration-300 transform hover:scale-105 ${
                    viewIntensity === 'medium'
                      ? 'bg-blue-500 text-white border-3 border-black shadow-lg'
                      : 'bg-white text-blue-600 border-3 border-blue-500 hover:bg-blue-50'
                  }`}
                  style={{
                    boxShadow: viewIntensity === 'medium' 
                      ? '4px 4px 0px var(--color-primary-black)' 
                      : '3px 3px 0px #3b82f6'
                  }}
                >
                  Balanced
                </button>
                
                <button
                  type="button"
                  onClick={() => setViewIntensity('intense')}
                  className={`arteme-button flex-1 lg:w-full py-3 px-4 font-bold text-base transition-all duration-300 transform hover:scale-105 ${
                    viewIntensity === 'intense'
                      ? 'bg-red-500 text-white border-3 border-black shadow-lg'
                      : 'bg-white text-red-600 border-3 border-red-500 hover:bg-red-50'
                  }`}
                  style={{
                    boxShadow: viewIntensity === 'intense' 
                      ? '4px 4px 0px var(--color-primary-black)' 
                      : '3px 3px 0px #ef4444'
                  }}
                >
                  Immersive
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Statistics */}
      <div className="max-w-4xl mx-auto mb-6 mx-8">
        <div className="arteme-card p-4">
          <h2 className="arteme-title text-lg mb-3">Plan Overview</h2>
          <div className="grid grid-cols-4 gap-3">
            <div className="text-center">
              <div className="text-xl font-bold arteme-title">{displayStatistics.total_items}</div>
              <div className="text-xs">Items</div>
            </div>
            <div className="text-center">
              <div className="text-xl font-bold arteme-title">{displayStatistics.weeks}</div>
              <div className="text-xs">Weeks</div>
            </div>
            <div className="text-center">
              <div className="text-xl font-bold arteme-title">{displayStatistics.total_time_hours}h</div>
              <div className="text-xs">Total Time</div>
            </div>
            <div className="text-center">
              <div className="text-xl font-bold arteme-title">{displayStatistics.avg_hours_per_week}h</div>
              <div className="text-xs">Per Week</div>
            </div>
          </div>
        </div>
      </div>

      {/* Weekly Plan - Horizontal Layout */}
      <div className="w-full px-8 lg:px-16 mx-8">
        <div className="max-w-7xl mx-auto">
          <div className="space-y-12">
            {getMonthHeaders().map((month) => (
              <div key={month} className="arteme-card p-6 lg:p-8">
                {/* Month Header */}
                <div className="text-center mb-8">
                  <h3 className="arteme-title text-2xl lg:text-3xl mb-4" style={{ color: 'var(--color-primary-black)' }}>
                    Month {month}
                  </h3>
                  <div className="w-24 h-1 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full mx-auto"></div>
                </div>

                {/* Weekly Layout - 4 weeks side by side horizontally */}
                <div className="grid grid-cols-4 gap-4">
                  {Array.from({length: 4}, (_, weekInMonth) => {
                    const globalWeek = (month - 1) * 4 + weekInMonth + 1;
                    const maxWeeks = viewDuration * 4;
                    
                    // Skip weeks beyond selected duration
                    if (globalWeek > maxWeeks) {
                      return (
                        <div key={`empty-${weekInMonth}`} className="bg-gray-100 border-2 border-gray-200 rounded-xl p-4 opacity-50">
                          <div className="text-center text-gray-400">
                            <h4 className="font-bold text-sm mb-2">Week {globalWeek}</h4>
                            <p className="text-xs">Beyond selected duration</p>
                          </div>
                        </div>
                      );
                    }
                    
                    const weekKey = `week_${globalWeek}`;
                    const items = displayPlan?.[weekKey] || [];
                    
                    return (
                      <div key={weekKey} className="bg-white border-2 border-gray-300 rounded-lg hover:shadow-lg transition-all flex flex-col" style={{ minHeight: '280px' }}>
                        {/* Week Header */}
                        <div className="p-2 border-b border-gray-200 flex-shrink-0">
                          <div className="text-center">
                            <h4 className="arteme-title text-xs font-bold mb-1" style={{ color: 'var(--color-primary-black)' }}>
                              Week {globalWeek}
                            </h4>
                            <span className="bg-purple-100 text-purple-700 text-xs px-1.5 py-0.5 rounded-full font-medium">
                              {items.length} items
                            </span>
                          </div>
                        </div>
                        
                        {/* Week Content - Items stacked vertically */}
                        <div className="flex-1 p-2 overflow-y-auto">
                          {items.length === 0 ? (
                            <div className="text-center py-4 text-gray-500">
                              <p className="text-xs">No items scheduled</p>
                            </div>
                          ) : (
                            <div className="space-y-1.5">
                              {items.slice(0, 4).map((item, index) => {
                                const typeColors: { [key: string]: string } = {
                                  'art': 'bg-purple-50 text-purple-700 border-purple-200',
                                  'movies': 'bg-blue-50 text-blue-700 border-blue-200',
                                  'movie': 'bg-blue-50 text-blue-700 border-blue-200',
                                  'books': 'bg-green-50 text-green-700 border-green-200',
                                  'book': 'bg-green-50 text-green-700 border-green-200',
                                  'music': 'bg-yellow-50 text-yellow-700 border-yellow-200',
                                  'poetry': 'bg-pink-50 text-pink-700 border-pink-200',
                                  'podcasts': 'bg-indigo-50 text-indigo-700 border-indigo-200',
                                  'podcast': 'bg-indigo-50 text-indigo-700 border-indigo-200',
                                  'musicals': 'bg-red-50 text-red-700 border-red-200',
                                  'musical': 'bg-red-50 text-red-700 border-red-200'
                                };
                                
                                const typeColor = typeColors[item.type?.toLowerCase()] || 'bg-gray-50 text-gray-700 border-gray-200';
                                
                                // Calculate estimated time for this item
                                const itemType = item.type?.toLowerCase() || 'art';
                                let estimatedHours = 2.0; // Default
                                if (itemType.includes('art') || itemType.includes('poetry')) {
                                  estimatedHours = 1.0;
                                } else if (itemType.includes('book')) {
                                  estimatedHours = 8.0;
                                } else if (itemType.includes('movie') || itemType.includes('musical')) {
                                  estimatedHours = 2.5;
                                } else if (itemType.includes('music') || itemType.includes('podcast')) {
                                  estimatedHours = 1.5;
                                }
                                
                                return (
                                  <div key={item.id || `${globalWeek}-${index}`} className={`p-1.5 rounded border ${typeColor} hover:shadow-sm transition-shadow`}>
                                    <div className="flex items-start justify-between mb-0.5">
                                      <h5 className="font-medium text-xs leading-tight flex-1 pr-1" title={item.title}>
                                        {item.title.length > 14 ? `${item.title.substring(0, 14)}...` : item.title}
                                      </h5>
                                      <span className="text-xs opacity-75 flex-shrink-0 font-semibold">
                                        {item.type?.charAt(0).toUpperCase()}
                                      </span>
                                    </div>
                                    
                                    {item.creator && (
                                      <p className="text-xs opacity-75 truncate mb-0.5" title={item.creator}>
                                        {item.creator.length > 11 ? `${item.creator.substring(0, 11)}...` : item.creator}
                                      </p>
                                    )}
                                    
                                    <div className="flex justify-start items-center text-xs">
                                      <span className="bg-gray-100 px-1 py-0.5 rounded text-gray-600 text-xs">
                                        {estimatedHours}h
                                      </span>
                                    </div>
                                  </div>
                                );
                              })}
                              
                              {items.length > 4 && (
                                <div className="text-center">
                                  <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded-full">
                                    +{items.length - 4} more
                                  </span>
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="text-center mt-12 mb-8 mx-8">
        <div className="arteme-card p-6 max-w-2xl mx-auto">
          <h3 className="arteme-title text-xl mb-3">Ready to Start Your Journey?</h3>
          <p className="text-gray-700 mb-4">
            Your personalized art journey has been carefully curated based on your preferences.<br />
            Each week offers a balanced mix of different art forms to enrich your cultural experience.
          </p>
          <button 
            onClick={() => toast.success('Your art journey begins now!')}
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