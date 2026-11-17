import { createHash } from 'node:crypto';

// Pinned JS SDK version and SRI hash used by <JsCdnScript />. Update with `npm run update-js-cdn-sri`.
export const pinnedFile = new URL('./pinned.json', import.meta.url);

export const cdnUrl = (version) => `https://cdn.jsdelivr.net/npm/@flagsmith/flagsmith@${version}/index.js`;

// Subresource Integrity hash (sha384) of the JS SDK bundle as served by jsDelivr.
export const fetchIntegrity = async (version) => {
    const response = await fetch(cdnUrl(version));
    if (!response.ok) throw new Error(`${cdnUrl(version)}: HTTP ${response.status}`);
    const body = Buffer.from(await response.arrayBuffer());
    return `sha384-${createHash('sha384').update(body).digest('base64')}`;
};
