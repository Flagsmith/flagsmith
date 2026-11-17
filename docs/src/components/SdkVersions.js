import { usePluginData } from '@docusaurus/useGlobalData';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import { maxSatisfying } from 'semver';
import { JS_SPEC } from './sdkVersionSpecs.js';

const Version = ({ sdk, spec = '*', options = {} }) => {
    const {
        siteConfig: {
            customFields: { CI },
        },
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

export const JavaVersion = ({ spec = '~8' }) => Version({ sdk: 'java', spec });
export const AndroidVersion = ({ spec = '~1' }) => Version({ sdk: 'android', spec });
export const CocoapodsVersion = ({ spec = '~3' }) => Version({ sdk: 'cocoapods', spec });
export const SwiftPMVersion = ({ spec = '~3' }) => Version({ sdk: 'swiftpm', spec });
export const DotnetVersion = ({ spec = '~8' }) => Version({ sdk: 'dotnet', spec });
export const ElixirVersion = ({ spec = '~2' }) => Version({ sdk: 'elixir', spec });
export const RustVersion = ({ spec = '~2' }) => Version({ sdk: 'rust', spec });
export const JsVersion = ({ spec = JS_SPEC }) => Version({ sdk: 'js', spec });
export const NodejsVersion = ({ spec = '^9' } = {}) => Version({ sdk: 'nodejs', spec });
export const FlutterVersion = ({ spec = '~6' }) => Version({ sdk: 'flutter', spec });

// `<script>` tag that loads the JS SDK from jsDelivr, pinned to an exact version with a Subresource Integrity hash.
export const JsCdnScript = () => {
    const {
        siteConfig: {
            customFields: { CI },
        },
    } = useDocusaurusContext();
    const script = usePluginData('flagsmith-versions').jsCdnScript;
    if (!script) {
        const message = 'no jsDelivr script found for the JS SDK';
        if (CI) throw new Error(message);
        console.error(message);
        return '<script src="https://cdn.jsdelivr.net/npm/@flagsmith/flagsmith@x.y.z/index.js"></script>';
    }
    return `<script src="${script.src}" integrity="${script.integrity}" crossorigin="anonymous"></script>`;
};
