import Constants from 'common/constants'

// Same shape as the React snippet, but React Native has no <div>/<p>, so this
// renders View/Text. Flag names are user-defined and need not be valid JS
// identifiers, so flags are read by key with local variable names.
export default (
  envId,
  { FEATURE_NAME, FEATURE_NAME_ALT, LIB_NAME, NPM_CLIENT },
) => `import ${LIB_NAME} from "${NPM_CLIENT}";
import { FlagsmithProvider, useFlags } from '${NPM_CLIENT}/react';
import { View, Text } from 'react-native';

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
    <View>
      <Text>${FEATURE_NAME} enabled: {String(isEnabled)}</Text>
      <Text>${
        FEATURE_NAME_ALT || FEATURE_NAME
      } value: {String(featureValue)}</Text>
    </View>
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
