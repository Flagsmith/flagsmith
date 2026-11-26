import type { Metadata } from 'next';
import type { ReactNode } from 'react';
import './globals.css';

export const metadata: Metadata = {
    title: 'StudyStreak',
    description: 'Build a daily study habit and keep your streak alive.',
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
    return (
        <html lang="en">
            <body>{children}</body>
        </html>
    );
}
