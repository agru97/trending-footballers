"use client";

import { Search } from "lucide-react";

export default function SearchPage() {
  return (
    <div className="min-h-screen w-full bg-brand flex items-center justify-center p-4">
      <div className="w-[320px] xs:w-[375px] sm:w-[410px] bg-white/95 backdrop-blur-xl rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.12)] p-6 border border-white/20">
        <div className="text-center space-y-4">
          <div className="mx-auto w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center">
            <Search className="w-8 h-8 text-brand" />
          </div>
          <h1 className="text-2xl font-bold text-gray-800">Player Search</h1>
          <p className="text-gray-500">
            Coming soon! Search for any football player and track their trending status.
          </p>
          <div className="mt-8 space-y-4">
            <div className="bg-gray-50 p-4 rounded-xl">
              <h3 className="font-medium text-gray-700">Planned Features:</h3>
              <ul className="mt-2 space-y-2 text-sm text-gray-600">
                <li>• Real-time player search</li>
                <li>• Historical trend data</li>
                <li>• Advanced filters by league, team, and position</li>
                <li>• Player comparison tools</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 