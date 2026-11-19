import { defineConfig } from 'vite';

export default defineConfig({
    base: './',
    server: {
        port: 5173,
        proxy: {
            '^/api/v1/(flags|identities|events)(/|\\?|$)': {
                target: 'http://127.0.0.1:8000',
                changeOrigin: true,
            },
        },
    },
});
