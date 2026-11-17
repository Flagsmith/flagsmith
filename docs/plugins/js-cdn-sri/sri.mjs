import { createHash } from 'node:crypto';
import { readdir, readFile } from 'node:fs/promises';

// Docs pages whose jsDelivr `<script>` snippets must carry a Subresource Integrity hash.
export const docsDir = new URL('../../docs/', import.meta.url);

// jsDelivr snippets are marked with the comment Renovate uses to bump them (see `customManagers` in renovate.json),
// directly above the code block (in an .mdx file, so Prettier keeps the comment intact):
//
//   {/* renovate: datasource=npm depName=@flagsmith/flagsmith */}
//
//   ```html
//   <script src="https://cdn.jsdelivr.net/npm/@flagsmith/flagsmith@1.2.3/index.js" integrity="sha384-..." crossorigin="anonymous"></script>
//   ```
//
// Inside a marked block the tag must have exactly this form: an exact version and file path, so the file can't change
// under the hash (https://www.jsdelivr.com/using-sri-with-dynamic-files), then `integrity` and `crossorigin`.
// The block must open with exactly three backticks, and ends at the first line that could close it (a fence indented by up
// to three spaces, per CommonMark).
const markedBlock = /\{\/\* renovate: datasource=npm depName=(\S+) \*\/\}\r?\n\s*```[^`\n]*\n([\s\S]*?)\r?\n {0,3}```/g;
const marker = /\{\/\*\s*renovate:/gi;
const escape = (s) => s.replace(/[.*+?^${}()|[\]\\/]/g, '\\$&');
const snippetTag = (depName) =>
    new RegExp(
        `<script src="(https://cdn\\.jsdelivr\\.net/npm/${escape(depName)}@\\d+\\.\\d+\\.\\d+(?:-[0-9A-Za-z.-]+)?/[^"?#]+)"` +
            ` integrity="((?:sha256|sha384|sha512)-[A-Za-z0-9+/=]+)" crossorigin="anonymous"></script>`,
        'g',
    );
// Case-insensitive, like browsers treat hostnames, so no casing of the URL escapes the check.
const jsDelivr = /cdn\.jsdelivr\.net/gi;
export const snippetFormat =
    'each jsDelivr snippet must sit alone in a code block directly below ' +
    '`{/* renovate: datasource=npm depName=<package> */}`, and use `<script src="https://cdn.jsdelivr.net/npm/<package>@<x.y.z>/<file>" integrity="..." crossorigin="anonymous"></script>`';

export const listDocs = async () =>
    (await readdir(docsDir, { recursive: true }))
        .filter((file) => /\.mdx?$/.test(file))
        .map((file) => new URL(file, docsDir));

// Finds the marked jsDelivr snippets in a file. `valid` is false if any jsDelivr URL isn't in a marked snippet, or any
// marker isn't directly above a code block with exactly one snippet, so the build can reject it.
export const findSnippets = (text) => {
    const snippets = [];
    let valid = true;
    let blocks = 0;
    for (const [, depName, block] of text.matchAll(markedBlock)) {
        blocks += 1;
        const found = [...block.matchAll(snippetTag(depName))];
        if (found.length !== 1) valid = false;
        for (const [tag, src, integrity] of found) snippets.push({ tag, src, integrity });
    }
    if ((text.match(marker)?.length ?? 0) !== blocks) valid = false;
    if ((text.match(jsDelivr)?.length ?? 0) !== snippets.length) valid = false;
    return { snippets, valid };
};

export const algorithmOf = (integrity) => integrity.split('-')[0];

// SRI hash of a file as served by jsDelivr. Files are fetched once per URL.
const files = new Map();
export const fetchIntegrity = async (src, algorithm) => {
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
