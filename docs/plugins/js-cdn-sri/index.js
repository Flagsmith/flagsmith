import { fileURLToPath } from 'node:url';
import { algorithmOf, fetchIntegrity, findScripts, listDocs, readText } from './sri.mjs';

// Fails the build if a jsDelivr `<script>` snippet in the docs is missing an `integrity` attribute, or if its hash
// doesn't match the file jsDelivr serves. Fix hashes with `npm run update-cdn-sri`.
export default async function jsCdnSri() {
    return {
        name: 'js-cdn-sri',
        async loadContent() {
            const errors = [];
            for (const file of await listDocs()) {
                for (const { src, integrity } of findScripts(await readText(file))) {
                    const where = `${fileURLToPath(file)}: ${src}`;
                    if (!integrity) {
                        errors.push(`${where} has no integrity attribute`);
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
                    if (served !== integrity) errors.push(`${where} pins ${integrity}, but jsDelivr serves ${served}`);
                }
            }
            if (errors.length) {
                throw new Error(
                    `${errors.join('\n')}\nRun \`npm run update-cdn-sri\` if this is an intentional version bump; otherwise investigate.`,
                );
            }
        },
    };
}
