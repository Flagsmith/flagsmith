import { createHash } from 'node:crypto';
import { maxSatisfying } from 'semver';
import { JS_SPEC } from '../../src/components/sdkVersionSpecs.js';

const fetchJSON = async (url, options) => {
    const response = await fetch(url, options);
    if (!response.ok) throw new Error(await response.text());
    return response.json();
};

const userAgent = 'Flagsmith-Docs <support@flagsmith.com>';

const fallback = (value) => (promise) => {
    if (!process.env.CI)
        return promise.catch((e) => {
            console.error(e);
            return value;
        });
    return promise;
};

const fetchMavenVersions = async ({ groupId, artifactId }) => {
    const response = await fetch(
        `https://repo1.maven.org/maven2/${groupId.replaceAll('.', '/')}/${artifactId}/maven-metadata.xml`,
    );
    if (!response.ok) throw new Error(await response.text());
    const xml = await response.text();
    return [...xml.matchAll(/<version>([^<]+)<\/version>/g)].map((match) => match[1]);
};

const fetchJavaVersions = async () =>
    fetchMavenVersions({
        groupId: 'com.flagsmith',
        artifactId: 'flagsmith-java-client',
    });

const fetchGitHubReleases = async (repo) => {
    const data = await fetchJSON(`https://api.github.com/repos/${repo}/releases`);
    return data.map((release) => (release.tag_name.startsWith('v') ? release.tag_name.slice(1) : release.tag_name));
};

const fetchAndroidVersions = async () =>
    fetchMavenVersions({
        groupId: 'com.flagsmith',
        artifactId: 'flagsmith-kotlin-android-client',
    });

const fetchSwiftPMVersions = async () => fetchGitHubReleases('Flagsmith/flagsmith-ios-client');

const fetchCocoapodsVersions = async () => {
    // retrieved from https://cocoapods.org/pods/FlagsmithClient
    const data = await fetchJSON('https://api.github.com/repos/CocoaPods/Specs/contents/Specs/2/8/0/FlagsmithClient');
    return data.map((entry) => entry.name);
};

const fetchDotnetVersions = async () => {
    const data = await fetchJSON('https://api.nuget.org/v3-flatcontainer/flagsmith/index.json');
    return data.versions;
};

const fetchRustVersions = async () => {
    // https://crates.io/data-access#api
    const headers = new Headers({
        'User-Agent': userAgent,
    });
    const data = await fetchJSON('https://crates.io/api/v1/crates/flagsmith', { headers });
    return data.versions.map((version) => version.num);
};

const fetchElixirVersions = async () => {
    const data = await fetchJSON('https://hex.pm/api/packages/flagsmith_engine');
    return data.releases.map((release) => release.version);
};

const fetchNpmVersions = async (pkg) => {
    const data = await fetchJSON(new URL(pkg, 'https://registry.npmjs.org'));
    return Object.keys(data.versions);
};

const fetchFlutterVersions = async () => {
    const data = await fetchJSON('https://pub.dev/api/packages/flagsmith', {
        headers: {
            Accept: 'application/vnd.pub.v2+json',
            'User-Agent': userAgent,
        },
    });
    return data.versions.map((v) => v.version);
};

// Subresource Integrity hash for the JS SDK bundle served by jsDelivr, so the docs can publish
// `<script integrity=...>` snippets that browsers refuse to run if the file is ever tampered with.
const fetchJsCdnScript = async (versions) => {
    const version = maxSatisfying(versions, JS_SPEC);
    if (!version) throw new Error(`no @flagsmith/flagsmith version matches ${JS_SPEC}`);
    const src = `https://cdn.jsdelivr.net/npm/@flagsmith/flagsmith@${version}/index.js`;
    const response = await fetch(src);
    if (!response.ok) throw new Error(await response.text());
    const body = Buffer.from(await response.arrayBuffer());
    const integrity = `sha384-${createHash('sha384').update(body).digest('base64')}`;
    return { src, integrity };
};

export default async function fetchFlagsmithVersions(context, options) {
    return {
        name: 'flagsmith-versions',
        async loadContent() {
            const [js, nodejs, java, android, swiftpm, cocoapods, dotnet, rust, elixir, flutter] = await Promise.all(
                [
                    fetchNpmVersions('@flagsmith/flagsmith'),
                    fetchNpmVersions('@flagsmith/nodejs'),
                    fetchJavaVersions(),
                    fetchAndroidVersions(),
                    fetchSwiftPMVersions(),
                    fetchCocoapodsVersions(),
                    fetchDotnetVersions(),
                    fetchRustVersions(),
                    fetchElixirVersions(),
                    fetchFlutterVersions(),
                ].map(fallback([])),
            );
            const jsCdnScript = await fallback(null)(fetchJsCdnScript(js));
            return {
                js,
                jsCdnScript,
                nodejs,
                java,
                android,
                swiftpm,
                cocoapods,
                dotnet,
                rust,
                elixir,
                flutter,
            };
        },
        async contentLoaded({ content, actions }) {
            const { setGlobalData } = actions;
            setGlobalData(content);
        },
    };
}
