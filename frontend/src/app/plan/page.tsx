'use client';

import ThreeMonthPlan from '@/components/ThreeMonthPlan';

export default function PlanPage() {
  // Use a test UUID - in real app, this would come from authentication
  const testUuid = 'test-uuid-123';
  
  return (
    <main className="min-h-screen">
      <ThreeMonthPlan userUuid={testUuid} />
    </main>
  );
}