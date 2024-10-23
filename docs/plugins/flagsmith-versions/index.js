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

const fetchJavaVersion = async () => {
    const data = await fetchJSON(
        'https://search.maven.org/solrsearch/select?q=g:%22com.flagsmith%22+AND+a:%22flagsmith-java-client%22&wt=json',
    );
    if (data.response.numFound !== 1) throw new Error('unexpected response when fetching Java version', data);
    return data.response.docs[0].latestVersion;
};

const fetchDotnetVersion = async () => {
    const data = await fetchJSON('https://api.nuget.org/v3-flatcontainer/Flagsmith/index.json');
    return data.versions[data.versions.length - 1];
};

const fetchRustVersion = async () => {
    // https://crates.io/data-access#api
    const headers = new Headers({
        'User-Agent': 'Flagsmith-Docs <support@flagsmith.com>',
    });
    const data = await fetchJSON('https://crates.io/api/v1/crates/flagsmith', { headers });
    return data.crate.max_stable_version;
};

const fetchElixirVersion = async () => {
    const data = await fetchJSON('https://hex.pm/api/packages/flagsmith_engine');
    return data.releases[0].version;
};

export default async function fetchFlagsmithVersions(context, options) {
    return {
        name: 'flagsmith-versions',
        async loadContent() {
            const [java, dotnet, rust, elixir] = await Promise.all(
                [fetchJavaVersion(), fetchDotnetVersion(), fetchRustVersion(), fetchElixirVersion()].map(
                    fallback('x.y.z'),
                ),
            );
            return {
                java,
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
