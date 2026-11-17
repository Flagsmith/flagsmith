// Sets the `integrity` attribute of every jsDelivr `<script>` snippet in the docs to the hash of the file it loads.
// Run after changing a snippet's version. Renovate runs it when bumping @flagsmith/flagsmith (see renovate.json).
import { writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { algorithmOf, fetchIntegrity, findScripts, listDocs, readText } from './sri.mjs';

for (const file of await listDocs()) {
    const text = await readText(file);
    let updated = text;
    for (const { tag, src, integrity } of findScripts(text)) {
        const hash = await fetchIntegrity(src, algorithmOf(integrity));
        if (hash === integrity) continue;
        const fixed = integrity
            ? tag.replace(`integrity="${integrity}"`, `integrity="${hash}"`)
            : tag.replace(`src="${src}"`, `src="${src}" integrity="${hash}" crossorigin="anonymous"`);
        updated = updated.replaceAll(tag, fixed);
        console.log(`${fileURLToPath(file)}: ${src} -> ${hash}`);
    }
    if (updated !== text) await writeFile(file, updated);
}
