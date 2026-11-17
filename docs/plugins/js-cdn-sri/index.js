import { readFile } from 'node:fs/promises';
import { cdnUrl, fetchIntegrity, pinnedFile } from './sri.mjs';

// Fails the build if the pinned hash doesn't match what jsDelivr serves, so a stale or tampered pin can't ship.
export default async function jsCdnSri() {
    return {
        name: 'js-cdn-sri',
        async loadContent() {
            const { version, integrity } = JSON.parse(await readFile(pinnedFile, 'utf8'));
            let served;
            try {
                served = await fetchIntegrity(version);
            } catch (e) {
                if (process.env.CI) throw e;
                console.error(`Could not verify the pinned JS SDK SRI hash: ${e}`);
                return;
            }
            if (served !== integrity) {
                throw new Error(
                    `${cdnUrl(version)} has integrity ${served}, but ${pinnedFile.pathname} pins ${integrity}. ` +
                        'Run `npm run update-js-cdn-sri` if this is an intentional SDK bump; otherwise investigate.',
                );
            }
        },
    };
}
