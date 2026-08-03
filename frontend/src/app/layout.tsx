import React from 'react';
import '../styles/globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Scribl.AI — Real-Time Multiplayer Drawing & Guessing',
  description: 'Production-grade real-time multiplayer drawing application powered by Next.js, Django Channels, and Redis.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased selection:bg-brand-500 selection:text-white min-h-screen bg-[#0b0f19]">
        {children}
      </body>
    </html>
  );
}
