// Pins <JsCdnScript /> to a JS SDK version and records its SRI hash.
// Usage: npm run update-js-cdn-sri [-- <version>]  (defaults to the npm `latest` dist-tag)
import { writeFile } from 'node:fs/promises';
import { fetchIntegrity, pinnedFile } from './sri.mjs';

let version = process.argv[2];
if (!version) {
    const response = await fetch('https://registry.npmjs.org/@flagsmith/flagsmith/latest');
    if (!response.ok) throw new Error(`npm registry: HTTP ${response.status}`);
    ({ version } = await response.json());
}
const integrity = await fetchIntegrity(version);
await writeFile(pinnedFile, JSON.stringify({ version, integrity }, null, 4) + '\n');
console.log(`Pinned @flagsmith/flagsmith@${version} (${integrity})`);
