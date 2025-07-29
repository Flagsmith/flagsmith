// src/crisp.js
import { useEffect } from 'react';
import { useLocation } from '@docusaurus/router';

export default function CrispLoader() {
    const location = useLocation();

    useEffect(() => {
        if (typeof window === 'undefined') {
            return;
        }

        window.$crisp = window.$crisp || [];
        window.CRISP_WEBSITE_ID = '8857f89e-0eb5-4263-ab49-a293872b6c19';

        if (!document.getElementById('crisp-chat-script')) {
            const d = document;
            const s = d.createElement('script');
            s.id = 'crisp-chat-script';
            s.src = 'https://client.crisp.chat/l.js';
            s.async = 1;
            d.head.appendChild(s);
        }

        const kapaEl = document.getElementById('kapa-widget-container');

        if (location.pathname.replace(/\//g, '') === 'support') {
            window.$crisp.push(['do', 'chat:show']);
            window.__isCrispVisible = true;
            if (kapaEl) kapaEl.style.display = 'none';
        } else {
            window.$crisp.push(['do', 'chat:hide']);
            window.__isCrispVisible = false;
            if (kapaEl) kapaEl.style.display = '';
        }
    }, [location.pathname]);

    return null;
}
