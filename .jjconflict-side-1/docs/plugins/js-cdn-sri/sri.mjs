import { createHash } from 'node:crypto';
import { readdir, readFile } from 'node:fs/promises';
import { gunzipSync } from 'node:zlib';

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
        `<script src="(https://cdn\\.jsdelivr\\.net/npm/${escape(depName)}@(\\d+\\.\\d+\\.\\d+(?:-[0-9A-Za-z.-]+)?)/([^"?#]+))"` +
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
        for (const [tag, src, version, file, integrity] of found) {
            snippets.push({ tag, src, integrity, depName, version, file });
        }
    }
    if ((text.match(marker)?.length ?? 0) !== blocks) valid = false;
    if ((text.match(jsDelivr)?.length ?? 0) !== snippets.length) valid = false;
    return { snippets, valid };
};

export const algorithmOf = (integrity) => integrity.split('-')[0];

// A hash or content mismatch that must fail the build even when offline errors are tolerated.
export class IntegrityError extends Error {}

// SRI hash of a snippet's file. The hash comes from the npm release, not from jsDelivr: the tarball is checked against
// the registry's `dist.integrity`, the file is extracted from it, and jsDelivr must serve exactly the same bytes.
// Snippets are verified once per URL.
const verified = new Map();
export const fetchIntegrity = async (snippet, algorithm) => {
    if (!verified.has(snippet.src)) verified.set(snippet.src, verifiedFile(snippet));
    return `${algorithm}-${createHash(algorithm)
        .update(await verified.get(snippet.src))
        .digest('base64')}`;
};

const verifiedFile = async ({ src, depName, version, file }) => {
    const [fromNpm, fromJsDelivr] = await Promise.all([npmFile(depName, version, file), fetchBytes(src)]);
    if (!fromNpm.equals(fromJsDelivr)) {
        throw new IntegrityError(`${src} doesn't match ${file} in the npm release of ${depName}@${version}`);
    }
    return fromNpm;
};

const npmFile = async (depName, version, file) => {
    const { dist } = await fetchJson(`https://registry.npmjs.org/${depName}/${version}`);
    const tarball = await fetchBytes(dist.tarball);
    const [algorithm, expected] = dist.integrity.split(/-(.*)/s);
    if (createHash(algorithm).update(tarball).digest('base64') !== expected) {
        throw new IntegrityError(`${dist.tarball} doesn't match its registry integrity ${dist.integrity}`);
    }
    const contents = untar(gunzipSync(tarball)).get(file);
    if (!contents) throw new IntegrityError(`${depName}@${version} has no file ${file}`);
    return contents;
};

// Minimal tar reader for npm tarballs: maps each file path, without the top-level directory, to its contents.
const untar = (tar) => {
    const files = new Map();
    let longName = null;
    for (let offset = 0; offset + 512 <= tar.length; ) {
        const header = tar.subarray(offset, offset + 512);
        if (header.every((byte) => byte === 0)) break;
        const field = (start, length) => header.toString('utf8', start, start + length).replace(/\0.*$/s, '');
        const size = parseInt(field(124, 12).trim() || '0', 8);
        const type = field(156, 1);
        const body = tar.subarray(offset + 512, offset + 512 + size);
        offset += 512 + Math.ceil(size / 512) * 512;
        if (type === 'x') {
            longName = body.toString('utf8').match(/^\d+ path=(.*)$/m)?.[1] ?? longName;
        } else if (type === 'L') {
            longName = body.toString('utf8').replace(/\0.*$/s, '');
        } else {
            const prefix = field(345, 155);
            const name = longName ?? (prefix ? `${prefix}/${field(0, 100)}` : field(0, 100));
            longName = null;
            if (type === '0' || type === '') files.set(name.replace(/^[^/]+\//, ''), Buffer.from(body));
        }
    }
    return files;
};

const fetchBytes = async (url) => {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`${url}: HTTP ${response.status}`);
    return Buffer.from(await response.arrayBuffer());
};

const fetchJson = async (url) => {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`${url}: HTTP ${response.status}`);
    return response.json();
};

export const readText = (url) => readFile(url, 'utf8');
