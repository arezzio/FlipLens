import React from 'react';

export const ResponsiveTest: React.FC = () => {
  return (
    <div className="fixed top-4 right-4 z-50 bg-black text-white p-2 rounded-lg text-xs font-mono">
      <div className="block sm:hidden">Mobile (xs)</div>
      <div className="hidden sm:block md:hidden">Small (sm)</div>
      <div className="hidden md:block lg:hidden">Medium (md)</div>
      <div className="hidden lg:block xl:hidden">Large (lg)</div>
      <div className="hidden xl:block 2xl:hidden">XL (xl)</div>
      <div className="hidden 2xl:block">2XL (2xl)</div>
    </div>
  );
}; 