import { Features } from '@/components/Features';
import { Hero } from '@/components/Hero';
import { HowItWorks } from '@/components/HowItWorks';
import { SiteFooter } from '@/components/SiteFooter';
import { SiteHeader } from '@/components/SiteHeader';

export default function HomePage() {
    return (
        <>
            <SiteHeader />
            <main>
                <Hero />
                <Features />
                <HowItWorks />
            </main>
            <SiteFooter />
        </>
    );
}
