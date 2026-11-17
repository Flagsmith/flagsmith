import { fileURLToPath } from 'node:url';
import { algorithmOf, fetchIntegrity, findScripts, isImmutable, listDocs, readText } from './sri.mjs';

// Fails the build if a jsDelivr `<script>` snippet in the docs doesn't load an exact version and file, is missing
// `integrity` or `crossorigin`, or has a hash that doesn't match the file jsDelivr serves.
// Fix hashes with `npm run update-cdn-sri`.
export default async function jsCdnSri() {
    return {
        name: 'js-cdn-sri',
        async loadContent() {
            const errors = [];
            let fixable = false;
            for (const file of await listDocs()) {
                for (const { src, integrity, hasCrossorigin } of findScripts(await readText(file))) {
                    const where = `${fileURLToPath(file)}: ${src}`;
                    if (!isImmutable(src)) {
                        errors.push(`${where} must load an exact version and file path, e.g. pkg@1.2.3/index.js`);
                        continue;
                    }
                    if (!integrity || !hasCrossorigin) {
                        fixable = true;
                        errors.push(`${where} needs both integrity and crossorigin attributes`);
                        continue;
                    }
                    let served;
                    try {
                        served = await fetchIntegrity(src, algorithmOf(integrity));
                    } catch (e) {
                        if (process.env.CI) throw e;
                        console.error(`Could not verify SRI hash for ${where}: ${e}`);
                        continue;
                    }
                    if (served !== integrity) {
                        fixable = true;
                        errors.push(`${where} pins ${integrity}, but jsDelivr serves ${served}`);
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
