import type { Metadata } from 'next';
import { cookies } from 'next/headers';
import type { ReactNode } from 'react';
import { readFlagsmithClientConfig } from '@/lib/env';
import { readVisitorId } from '@/lib/visitor-id';
import { Providers } from './providers';
import './globals.css';

export const metadata: Metadata = {
    title: 'StudyStreak',
    description: 'Build better study habits with a simple daily streak.',
};

export default async function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
    const visitorId = readVisitorId(await cookies());
    const flagsmithConfig = readFlagsmithClientConfig();
    if (!flagsmithConfig.ok) {
        console.error(`Flagsmith is disabled: ${flagsmithConfig.reason}`);
    }

    return (
        <html lang="en">
            <body className="bg-white font-sans text-slate-900 antialiased">
                <Providers
                    environmentKey={flagsmithConfig.ok ? flagsmithConfig.environmentKey : null}
                    visitorId={visitorId}
                >
                    {children}
                </Providers>
            </body>
        </html>
    );
}
