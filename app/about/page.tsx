"use client";

import { Info, Coffee, CreditCard, Github } from "lucide-react";

export default function AboutPage() {
  return (
    <div className="min-h-screen w-full bg-brand flex items-center justify-center p-4">
      <div className="w-[320px] xs:w-[375px] sm:w-[410px] bg-white/95 backdrop-blur-xl rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.12)] p-6 border border-white/20">
        <div className="text-center space-y-4">
          <div className="mx-auto w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center">
            <Info className="w-8 h-8 text-brand" />
          </div>
          <h1 className="text-2xl font-bold text-gray-800">About & Support</h1>
          <p className="text-gray-500">
            Trending Footballers tracks real-time popularity and trending status of football players worldwide.
          </p>

          <div className="mt-8 space-y-6">
            <div className="bg-gray-50 p-6 rounded-xl text-left">
              <h3 className="font-medium text-gray-700 mb-4">Support Our Platform</h3>
              <p className="text-sm text-gray-500 mb-6">
                Help us maintain and improve Trending Footballers! Your support helps cover our API costs,
                server expenses, and enables us to add more features.
              </p>
              
              <div className="space-y-3">
                <a
                  href="https://www.buymeacoffee.com/YOUR_USERNAME"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center justify-center gap-2 w-full px-4 py-2 bg-[#FFDD00] text-gray-900 rounded-lg hover:bg-[#FFDD00]/90 transition-colors"
                >
                  <Coffee className="w-5 h-5" />
                  <span className="font-medium">Buy us a coffee</span>
                </a>
                
                <a
                  href="https://www.paypal.com/donate/?hosted_button_id=YOUR_BUTTON_ID"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center justify-center gap-2 w-full px-4 py-2 bg-[#0070BA] text-white rounded-lg hover:bg-[#003087] transition-colors"
                >
                  <CreditCard className="w-5 h-5" />
                  <span className="font-medium">Donate with PayPal</span>
                </a>

                <a
                  href="https://github.com/YOUR_USERNAME/trending-footballers"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center justify-center gap-2 w-full px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 transition-colors"
                >
                  <Github className="w-5 h-5" />
                  <span className="font-medium">Star on GitHub</span>
                </a>
              </div>
            </div>

            <div className="text-center text-sm text-gray-500">
              <p>Every contribution helps us maintain and enhance the platform.</p>
              <p className="mt-1">Thank you for your support! 🙏</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 