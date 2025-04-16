"use client";

import { Star, Trophy, Globe, ChartLine } from "lucide-react";

export default function FavoritesPage() {
  return (
    <div className="min-h-screen w-full bg-brand flex items-center justify-center p-4">
      <div className="w-[320px] xs:w-[375px] sm:w-[410px] bg-white/95 backdrop-blur-xl rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.12)] p-6 border border-white/20">
        <div className="text-center space-y-4">
          <div className="mx-auto w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center">
            <Star className="w-8 h-8 text-brand" />
          </div>
          <h1 className="text-2xl font-bold text-gray-800">Coming Soon</h1>
          <p className="text-gray-500">
            We're working on exciting new features to enhance your experience!
          </p>
          <div className="mt-8 space-y-6">
            <div className="grid grid-cols-1 gap-4">
              <div className="bg-gray-50 p-4 rounded-xl flex items-start space-x-4">
                <div className="bg-blue-100 p-2 rounded-lg">
                  <Trophy className="w-6 h-6 text-brand" />
                </div>
                <div className="text-left">
                  <h3 className="font-medium text-gray-700">Player Rankings</h3>
                  <p className="text-sm text-gray-500 mt-1">
                    Track your favorite players' performance and trending status
                  </p>
                </div>
              </div>
              
              <div className="bg-gray-50 p-4 rounded-xl flex items-start space-x-4">
                <div className="bg-blue-100 p-2 rounded-lg">
                  <Globe className="w-6 h-6 text-brand" />
                </div>
                <div className="text-left">
                  <h3 className="font-medium text-gray-700">Global Coverage</h3>
                  <p className="text-sm text-gray-500 mt-1">
                    Expanding to more leagues and competitions worldwide
                  </p>
                </div>
              </div>
              
              <div className="bg-gray-50 p-4 rounded-xl flex items-start space-x-4">
                <div className="bg-blue-100 p-2 rounded-lg">
                  <ChartLine className="w-6 h-6 text-brand" />
                </div>
                <div className="text-left">
                  <h3 className="font-medium text-gray-700">Advanced Analytics</h3>
                  <p className="text-sm text-gray-500 mt-1">
                    Detailed statistics and trend analysis coming soon
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 