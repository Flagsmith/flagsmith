import Constants from 'common/constants'

// Flag names are user-defined and need not be valid JS identifiers, so the
// snippet reads flags by key and keeps its own local variable names.
export default (
  envId,
  { FEATURE_NAME, FEATURE_NAME_ALT, LIB_NAME, NPM_CLIENT },
) => `import ${LIB_NAME} from "${NPM_CLIENT}";
import { FlagsmithProvider, useFlags } from '${NPM_CLIENT}/react';

export function HomePage() {
  // Only re-renders when the listed flag values / traits change
  const flags = useFlags([${
    FEATURE_NAME_ALT
      ? `'${FEATURE_NAME}', '${FEATURE_NAME_ALT}'`
      : `'${FEATURE_NAME}'`
  }]);
  const isEnabled = flags['${FEATURE_NAME}'].enabled;
  const featureValue = flags['${FEATURE_NAME_ALT || FEATURE_NAME}'].value;

  return (
    <div>
      <p>${FEATURE_NAME} enabled: {String(isEnabled)}</p>
      <p>${FEATURE_NAME_ALT || FEATURE_NAME} value: {String(featureValue)}</p>
    </div>
  );
}

export default function App() {
  return (
    <FlagsmithProvider
      options={{
        environmentID: '${envId}',${
  Constants.isCustomFlagsmithUrl()
    ? `\n        api: '${Constants.getFlagsmithSDKUrl()}',`
    : ''
}
      }}
      flagsmith={${LIB_NAME}}>
      <HomePage />
    </FlagsmithProvider>
  );
}`
