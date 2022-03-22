module.exports = (envId, { LIB_NAME, FEATURE_NAME, FEATURE_FUNCTION, FEATURE_NAME_ALT, FEATURE_NAME_ALT_VALUE, NPM_CLIENT }, customFeature) => `// pages/_app.js
import ${LIB_NAME} from "${NPM_CLIENT}";
import { FlagsmithProvider } from 'flagsmith/react';

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

App.getInitialProps = async () => {
  await flagsmith.init({ // fetches flags on the server and passes them to the App 
      environmentID,
  });
  return { flagsmithState: flagsmith.getState() }
}

// pages/index.js
import flagsmith from 'flagsmith';
import { useFlags, useFlagsmith } from 'flagsmith/react';

export default function HomePage() {
  const flags = useFlags(['${FEATURE_NAME}','${FEATURE_NAME_ALT}']]); // only causes re-render if specified flag values / traits change
  const ${FEATURE_NAME} = flags.${FEATURE_NAME}.enabled
  const ${FEATURE_NAME_ALT} = flags.${FEATURE_NAME_ALT}.value
  return (
    &lt;>{...}&lt;/>
  );
}`;
