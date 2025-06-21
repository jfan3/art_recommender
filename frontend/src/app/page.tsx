'use client';

import Chat from '@/components/Chat';

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8 bg-gray-900 text-white">
      <div className="text-center mb-8">
        <h1 className="text-4xl font-bold">Art Recommender</h1>
        <p className="text-gray-400">Your personal entertainment planner</p>
      </div>
      <Chat />
    </main>
  );
}
