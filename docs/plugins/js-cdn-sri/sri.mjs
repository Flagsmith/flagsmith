import { createHash } from 'node:crypto';
import { readdir, readFile } from 'node:fs/promises';

// Docs pages whose jsDelivr `<script>` snippets must carry a Subresource Integrity hash.
export const docsDir = new URL('../../docs/', import.meta.url);

// `<script src="https://cdn.jsdelivr.net/npm/...">` tags, capturing the URL and the remaining attributes.
const scriptTag = /<script\s+src="(https:\/\/cdn\.jsdelivr\.net\/npm\/[^"]+)"([^>]*)>/g;
const integrityAttr = /\sintegrity="([^"]*)"/;

export const listDocs = async () =>
    (await readdir(docsDir, { recursive: true }))
        .filter((file) => /\.mdx?$/.test(file))
        .map((file) => new URL(file, docsDir));

// Finds every jsDelivr script tag in a file, with its `integrity` value (or null if missing).
export const findScripts = (text) =>
    [...text.matchAll(scriptTag)].map(([tag, src, attrs]) => ({
        tag,
        src,
        integrity: attrs.match(integrityAttr)?.[1] ?? null,
    }));

// Algorithm of an SRI value such as `sha384-...`, defaulting to sha384 for new hashes.
export const algorithmOf = (integrity) => integrity?.match(/^(sha256|sha384|sha512)-/)?.[1] ?? 'sha384';

// SRI hash of a file as served by jsDelivr. Files are fetched once per URL.
const files = new Map();
export const fetchIntegrity = async (src, algorithm = 'sha384') => {
    if (!files.has(src)) files.set(src, fetchFile(src));
    return `${algorithm}-${createHash(algorithm)
        .update(await files.get(src))
        .digest('base64')}`;
};

const fetchFile = async (src) => {
    const response = await fetch(src);
    if (!response.ok) throw new Error(`${src}: HTTP ${response.status}`);
    return Buffer.from(await response.arrayBuffer());
};

export const readText = (url) => readFile(url, 'utf8');
