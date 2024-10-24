import { usePluginData } from '@docusaurus/useGlobalData';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import { maxSatisfying } from 'semver';

export const Version = ({ sdk, spec = '*' }) => {
    const {
        siteConfig: { CI },
    } = useDocusaurusContext();
    const versions = usePluginData('flagsmith-versions')[sdk];
    if (!versions) throw new Error('unknown sdk: ' + sdk);
    const latest = maxSatisfying(versions, spec);
    if (latest === null) {
        const message = `no version found for ${sdk} that matches ${spec}. available versions: [${versions.join(', ')}]`;
        if (CI) throw new Error(message);
        console.error(message);
    }
    return latest ?? 'x.y.z';
};

export const JavaVersion = ({ spec = '~7' }) => Version({ sdk: 'java', spec });
export const DotnetVersion = ({ spec = '~5' }) => Version({ sdk: 'dotnet', spec });
export const ElixirVersion = ({ spec = '~2' }) => Version({ sdk: 'elixir', spec });
export const RustVersion = ({ spec = '~2' }) => Version({ sdk: 'rust', spec });
