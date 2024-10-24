const fetchJSON = async (url, options) => {
    const response = await fetch(url, options);
    if (!response.ok) throw new Error(await response.text());
    return response.json();
};

const fallback = (value) => (promise) => {
    if (!process.env.CI)
        return promise.catch((e) => {
            console.error(e);
            return value;
        });
    return promise;
};

const fetchMavenVersions = async ({ groupId, artifactId }) => {
    const data = await fetchJSON(
        `https://central.sonatype.com/solrsearch/select?q=g:${groupId}+AND+a:${artifactId}&wt=json&core=gav`,
    );
    return data.response.docs.map((doc) => doc.v);
};

const fetchJavaVersions = async () =>
    fetchMavenVersions({
        groupId: 'com.flagsmith',
        artifactId: 'flagsmith-java-client',
    });

const fetchAndroidVersions = async () =>
    fetchMavenVersions({
        groupId: 'io.flagsmith',
        artifactId: 'flagsmith-kotlin-android-client',
    });

const fetchIOSVersions = async () => {
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
        'User-Agent': 'Flagsmith-Docs <support@flagsmith.com>',
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

export default async function fetchFlagsmithVersions(context, options) {
    return {
        name: 'flagsmith-versions',
        async loadContent() {
            const [js, java, android, ios, dotnet, rust, elixir] = await Promise.all(
                [
                    fetchNpmVersions('flagsmith'),
                    fetchJavaVersions(),
                    fetchAndroidVersions(),
                    fetchIOSVersions(),
                    fetchDotnetVersions(),
                    fetchRustVersions(),
                    fetchElixirVersions(),
                ].map(fallback([])),
            );
            return {
                js,
                java,
                android,
                ios,
                dotnet,
                rust,
                elixir,
            };
        },
        async contentLoaded({ content, actions }) {
            const { setGlobalData } = actions;
            setGlobalData(content);
        },
    };
}
