import { next, rewrite } from '@vercel/functions';

const MARKDOWN_ACCEPT = /text\/markdown/i;

export const config = {
    matcher: ['/((?!api/|_next/|static/|img/|fonts/|assets/|favicon\\.ico|llms\\.txt|.*\\.[a-zA-Z0-9]+$).*)'],
};

export default function markdownNegotiation(request: Request) {
    const accept = request.headers.get('accept') ?? '';
    if (!MARKDOWN_ACCEPT.test(accept)) {
        return next();
    }

    const { pathname } = new URL(request.url);
    if (pathname.startsWith('//')) {
        return next();
    }

    if (pathname === '/') {
        const target = new URL(request.url);
        target.pathname = '/index.md';
        return rewrite(target);
    }

    const docPath = pathname.endsWith('/') ? pathname.slice(0, -1) : pathname;
    const target = new URL(request.url);
    target.pathname = `${docPath}.md`;
    return rewrite(target);
}
