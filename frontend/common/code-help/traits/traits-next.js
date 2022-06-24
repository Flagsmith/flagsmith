module.exports = (envId, { LIB_NAME, NPM_CLIENT, TRAIT_NAME, USER_FEATURE_FUNCTION, FEATURE_NAME, FEATURE_NAME_ALT }, USER_ID) => `
// Option 1: Identify clientside
//Home Page
import flagsmith from '${LIB_NAME}/isomorphic';
import { useFlags, useFlagsmith } from 'flagsmith/react';

export default function HomePage() {
  const flags = useFlags(['${FEATURE_NAME}','${FEATURE_NAME_ALT}']]); // only causes re-render if specified flag values / traits change
  const ${FEATURE_NAME} = flags.${FEATURE_NAME}.enabled
  const ${FEATURE_NAME_ALT} = flags.${FEATURE_NAME_ALT}.value

  const identify = () => {
    flagsmith.identify('${USER_ID}', {${TRAIT_NAME}:21}); // only causes re-render if the user has overrides / segment overrides for ${FEATURE_NAME} or ${FEATURE_NAME_ALT}
  };

  const setTrait = () => {
    ${LIB_NAME}.setTrait("${TRAIT_NAME}", 22 // only causes re-render if the user has overrides / segment overrides for ${FEATURE_NAME} or ${FEATURE_NAME_ALT}
  };

  return (
    &lt;>{...}&lt;/>
  );
}

//Option 2: Alternatively, if you wish to do this serverside

export default function App({ Component, pageProps, flagsmithState } {
  return (
    &lt;FlagsmithProvider
      serverState={flagsmithState}
      options={{
        environmentID: '${envId}',
      }}
      flagsmith={flagsmith}&gt;
        &lt;Component {...pageProps} />
    &lt;/FlagsmithProvider>
  );
}

MyApp.getInitialProps = async () => {
  // calls page's \`getInitialProps\` and fills \`appProps.pageProps\`
  await flagsmith.init({ // fetches flags on the server
      environmentID,
      preventFetch: true
  });
  await flagsmith.identify('${USER_ID}', {${TRAIT_NAME}: 21}); // Will hydrate the app with the user's flags
  await flagsmith.setTrait('${TRAIT_NAME}', 22); // Will hydrate the app with the user's flags, re-evaluating segments
  return { flagsmithState: flagsmith.getState() }
}
`;
