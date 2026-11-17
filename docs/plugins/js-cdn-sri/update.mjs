// Sets the `integrity` hash of every Renovate-marked jsDelivr snippet in the docs (see sri.mjs) to the hash of the
// file it loads. Renovate runs this after bumping a snippet's version (see renovate.json).
import { writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { algorithmOf, fetchIntegrity, findSnippets, listDocs, readText } from './sri.mjs';

for (const file of await listDocs()) {
    const text = await readText(file);
    let updated = text;
    for (const { tag, src, integrity } of findSnippets(text).snippets) {
        const hash = await fetchIntegrity(src, algorithmOf(integrity));
        if (hash === integrity) continue;
        updated = updated.replaceAll(tag, tag.replace(integrity, hash));
        console.log(`${fileURLToPath(file)}: ${src} -> ${hash}`);
    }
    if (updated !== text) await writeFile(file, updated);
}
