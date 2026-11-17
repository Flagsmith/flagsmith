import { createHash } from 'node:crypto';
import { readdir, readFile } from 'node:fs/promises';

// Docs pages whose jsDelivr `<script>` snippets must carry a Subresource Integrity hash.
export const docsDir = new URL('../../docs/', import.meta.url);

// Opening `<script>` tags, and their attributes in any order.
const scriptTag = /<script\b[^>]*>/gi;
const attr = (name) => new RegExp(`\\s${name}\\s*=\\s*(["'])(.*?)\\1`, 'i');
const srcAttr = attr('src');
const integrityAttr = attr('integrity');
// `crossorigin` may be a bare attribute, which means `anonymous`.
const crossoriginAttr = /\scrossorigin(?=[\s=>/])/i;

const jsDelivrNpm = /^https:\/\/cdn\.jsdelivr\.net\/npm\//;
// jsDelivr only serves a fixed file for an exact version and an explicit file path. Ranges, `latest` and default
// files can change, so they can't be pinned with SRI: https://www.jsdelivr.com/using-sri-with-dynamic-files
const immutableUrl =
    /^https:\/\/cdn\.jsdelivr\.net\/npm\/(?:@[^/@]+\/)?[^/@]+@\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?\/[^?#]+$/;
export const isImmutable = (src) => immutableUrl.test(src);

export const listDocs = async () =>
    (await readdir(docsDir, { recursive: true }))
        .filter((file) => /\.mdx?$/.test(file))
        .map((file) => new URL(file, docsDir));

// Finds every jsDelivr npm `<script>` tag in a file, with its `integrity` value (or null if missing) and whether it
// has a `crossorigin` attribute.
export const findScripts = (text) =>
    [...text.matchAll(scriptTag)]
        .map(([tag]) => ({
            tag,
            src: tag.match(srcAttr)?.[2],
            integrity: tag.match(integrityAttr)?.[2] ?? null,
            hasCrossorigin: crossoriginAttr.test(tag),
        }))
        .filter(({ src }) => src && jsDelivrNpm.test(src));

// Returns `tag` with its `integrity` set to `hash`, adding `crossorigin="anonymous"` if missing.
export const withIntegrity = (tag, hash) => {
    let fixed = integrityAttr.test(tag)
        ? tag.replace(integrityAttr, (_, quote) => ` integrity=${quote}${hash}${quote}`)
        : tag.replace(srcAttr, (match) => `${match} integrity="${hash}"`);
    if (!crossoriginAttr.test(fixed)) {
        fixed = fixed.replace(integrityAttr, (match) => `${match} crossorigin="anonymous"`);
    }
    return fixed;
};

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
