// Sets the `integrity` attribute of every jsDelivr `<script>` snippet in the docs to the hash of the file it loads.
// Run after changing a snippet's version. Renovate runs it when bumping @flagsmith/flagsmith (see renovate.json).
import { writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { algorithmOf, fetchIntegrity, findScripts, isImmutable, listDocs, readText, withIntegrity } from './sri.mjs';

for (const file of await listDocs()) {
    const text = await readText(file);
    let updated = text;
    for (const { tag, src, integrity, hasCrossorigin } of findScripts(text)) {
        if (!isImmutable(src)) {
            throw new Error(`${fileURLToPath(file)}: ${src} must load an exact version and file path to pin its hash`);
        }
        const hash = await fetchIntegrity(src, algorithmOf(integrity));
        if (hash === integrity && hasCrossorigin) continue;
        updated = updated.replaceAll(tag, withIntegrity(tag, hash));
        console.log(`${fileURLToPath(file)}: ${src} -> ${hash}`);
    }
    if (updated !== text) await writeFile(file, updated);
}
