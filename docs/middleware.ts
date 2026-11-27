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
    if (pathname === '/') {
        return rewrite(new URL('/index.md', request.url));
    }

    const docPath = pathname.endsWith('/') ? pathname.slice(0, -1) : pathname;
    return rewrite(new URL(`${docPath}.md`, request.url));
}
