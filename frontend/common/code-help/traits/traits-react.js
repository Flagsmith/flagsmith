import Constants from 'common/constants'

module.exports = (
  envId,
  { FEATURE_NAME, FEATURE_NAME_ALT, LIB_NAME, NPM_CLIENT, TRAIT_NAME, USER_ID },
  userId,
) => `
// Option 1: Initialise with an identity and traits
import { FlagsmithProvider } from '${NPM_CLIENT}/react';

export default function App() {
  return (
    &lt;FlagsmithProvider
      options={{
        environmentID: '${envId}',${
  Constants.isCustomFlagsmithUrl()
    ? `\n        api: '${Constants.getFlagsmithSDKUrl()}',`
    : ''
}
        identity: '${userId || USER_ID}',
        traits: {${TRAIT_NAME}: 21},
      }}
      flagsmith={flagsmith}&gt;
      {...Your app}
    &lt;/FlagsmithProvider>
  );
}

// Option 2: Set traits / identify after initialising
import flagsmith from '${NPM_CLIENT}';
import { useFlags, useFlagsmith } from '${NPM_CLIENT}/react';

export default function HomePage() {
  const flags = useFlags(['${FEATURE_NAME}','${FEATURE_NAME_ALT}']); // only causes re-render if specified flag values / traits change
  const ${FEATURE_NAME} = flags.${FEATURE_NAME}.enabled
  const ${FEATURE_NAME_ALT} = flags.${FEATURE_NAME_ALT}.value

  const identify = () => {
    flagsmith.identify('${
      userId || USER_ID
    }', {${TRAIT_NAME}:21}); // only causes re-render if the user has overrides / segment overrides for ${FEATURE_NAME} or ${FEATURE_NAME_ALT}
  };

  const setTrait = () => {
    ${LIB_NAME}.setTrait("${TRAIT_NAME}", 22); // only causes re-render if the user has overrides / segment overrides for ${FEATURE_NAME} or ${FEATURE_NAME_ALT}
  };

  return (
    &lt;>{...}&lt;/>
  );
}`
