import { usePluginData } from '@docusaurus/useGlobalData';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import { maxSatisfying } from 'semver';

const Version = ({ sdk, spec = '*', options = {} }) => {
    const {
        siteConfig: { CI },
    } = useDocusaurusContext();
    const versions = usePluginData('flagsmith-versions')[sdk];
    if (!versions) throw new Error('unknown sdk: ' + sdk);
    const latest = maxSatisfying(versions, spec, options);
    if (latest === null) {
        const message = `no version found for ${sdk} that matches ${spec}. available versions: [${versions.join(', ')}]`;
        if (CI) throw new Error(message);
        console.error(message);
    }
    return latest ?? 'x.y.z';
};

export const JavaVersion = ({ spec = '~7' }) => Version({ sdk: 'java', spec });
export const AndroidVersion = ({ spec = '~1' }) => Version({ sdk: 'android', spec });
export const IOSVersion = ({ spec = '~3' }) => Version({ sdk: 'ios', spec });
export const DotnetVersion = ({ spec = '~5' }) => Version({ sdk: 'dotnet', spec });
export const ElixirVersion = ({ spec = '~2' }) => Version({ sdk: 'elixir', spec });
export const RustVersion = ({ spec = '~2' }) => Version({ sdk: 'rust', spec });
export const JsVersion = ({ spec = '~7' }) => Version({ sdk: 'js', spec });
export const NodejsVersion = ({ spec } = { spec: '~4' }) => Version({ sdk: 'nodejs', spec });
