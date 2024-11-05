import Constants from 'common/constants'

module.exports = (
  envId,
  { FEATURE_NAME, FEATURE_NAME_ALT, LIB_NAME, NPM_CLIENT },
) => `// App root
import ${LIB_NAME} from "${NPM_CLIENT}";
import { FlagsmithProvider } from 'flagsmith/react';

export default function App() {
  return (
    &lt;FlagsmithProvider
      options={{
        environmentID: '${envId}',${
  Constants.isCustomFlagsmithUrl
    ? `\n        api: '${Constants.getFlagsmithSDKUrl()}',`
    : ''
}
      }}
      flagsmith={flagsmith}&gt;
      {...Your app}
    &lt;/FlagsmithProvider>
  );
}

// Home Page
import ${LIB_NAME} from '${NPM_CLIENT}';
import { useFlags, useFlagsmith } from '${NPM_CLIENT}/react';

export default function HomePage() {
  const flags = useFlags(['${FEATURE_NAME}','${FEATURE_NAME_ALT}']); // only causes re-render if specified flag values / traits change
  const ${FEATURE_NAME} = flags.${FEATURE_NAME}.enabled
  const ${FEATURE_NAME_ALT} = flags.${FEATURE_NAME_ALT}.value
  return (
    &lt;>{...}&lt;/>
  );
}`
