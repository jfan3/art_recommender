'use client';

import SwipeFlow from '@/components/SwipeFlow';

export default function TestSwipePage() {
  // Use a test UUID to test the swipe functionality
  const testUuid = 'test-uuid-123';
  
  return (
    <main 
      className="min-h-screen"
      style={{
        background: `var(--color-primary-red)`
      }}
    >
      <SwipeFlow userUuid={testUuid} />
    </main>
  );
}