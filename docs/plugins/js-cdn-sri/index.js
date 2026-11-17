import { fileURLToPath } from 'node:url';
import {
    algorithmOf,
    fetchIntegrity,
    findSnippets,
    IntegrityError,
    listDocs,
    readText,
    snippetFormat,
} from './sri.mjs';

// Fails the build if a jsDelivr URL in the docs isn't in a Renovate-marked snippet (see sri.mjs), if jsDelivr doesn't
// serve the same file as the npm release, or if a snippet's hash doesn't match that file.
// Fix hashes with `npm run update-cdn-sri`.
export default async function jsCdnSri() {
    return {
        name: 'js-cdn-sri',
        async loadContent() {
            const errors = [];
            let fixable = false;
            for (const file of await listDocs()) {
                const path = fileURLToPath(file);
                const { snippets, valid } = findSnippets(await readText(file));
                if (!valid) errors.push(`${path}: ${snippetFormat}`);
                for (const snippet of snippets) {
                    const { src, integrity } = snippet;
                    let served;
                    try {
                        served = await fetchIntegrity(snippet, algorithmOf(integrity));
                    } catch (e) {
                        if (process.env.CI || e instanceof IntegrityError) throw e;
                        console.error(`Could not verify SRI hash for ${path}: ${src}: ${e}`);
                        continue;
                    }
                    if (served !== integrity) {
                        fixable = true;
                        errors.push(`${path}: ${src} pins ${integrity}, but the npm release has ${served}`);
                    }
                }
            }
            if (errors.length) {
                const hint = fixable
                    ? '\nRun `npm run update-cdn-sri` if this is an intentional version bump; otherwise investigate.'
                    : '';
                throw new Error(errors.join('\n') + hint);
            }
        },
    };
}
