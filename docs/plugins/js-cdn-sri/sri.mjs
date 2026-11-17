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
const markedBlock = /\{\/\* renovate: datasource=npm depName=(\S+) \*\/\}\n\s*```[^\n]*\n([\s\S]*?)\n```/g;
const escape = (s) => s.replace(/[.*+?^${}()|[\]\\/]/g, '\\$&');
const snippetTag = (depName) =>
    new RegExp(
        `<script src="(https://cdn\\.jsdelivr\\.net/npm/${escape(depName)}@\\d+\\.\\d+\\.\\d+(?:-[0-9A-Za-z.-]+)?/[^"?#]+)"` +
            ` integrity="((?:sha256|sha384|sha512)-[A-Za-z0-9+/=]+)" crossorigin="anonymous"></script>`,
        'g',
    );
const jsDelivr = /cdn\.jsdelivr\.net/g;
export const snippetFormat =
    'jsDelivr snippets must sit in a code block directly below `{/* renovate: datasource=npm depName=<package> */}` ' +
    'and use `<script src="https://cdn.jsdelivr.net/npm/<package>@<x.y.z>/<file>" integrity="..." crossorigin="anonymous"></script>`';

export const listDocs = async () =>
    (await readdir(docsDir, { recursive: true }))
        .filter((file) => /\.mdx?$/.test(file))
        .map((file) => new URL(file, docsDir));

// Finds the marked jsDelivr snippets in a file. `unmarked` counts jsDelivr URLs that aren't in one, which the build
// rejects so no snippet escapes the check.
export const findSnippets = (text) => {
    const snippets = [];
    for (const [, depName, block] of text.matchAll(markedBlock)) {
        for (const [tag, src, integrity] of block.matchAll(snippetTag(depName))) {
            snippets.push({ tag, src, integrity });
        }
    }
    const unmarked = (text.match(jsDelivr)?.length ?? 0) - snippets.length;
    return { snippets, unmarked };
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
