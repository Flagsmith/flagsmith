import Constants from 'common/constants'
export default (
  envId,
  { FEATURE_NAME, FEATURE_NAME_ALT, LIB_NAME, NPM_CLIENT },
) => `// pages/_app.js
import ${LIB_NAME} from "${NPM_CLIENT}/isomorphic";
import { FlagsmithProvider } from '@flagsmith/flagsmith/react';

export default function App({ Component, pageProps, flagsmithState }) {
  return (
    <FlagsmithProvider
      serverState={flagsmithState}
      options={{
        environmentID: "${envId}",${
  Constants.isCustomFlagsmithUrl()
    ? `\n        api: "${Constants.getFlagsmithSDKUrl()}",`
    : ''
}
      }}
      flagsmith={flagsmith}>
        <Component {...pageProps} />
    </FlagsmithProvider>
  );
}

App.getInitialProps = async () => {
  await flagsmith.init({ // fetches flags on the server and passes them to the App 
      environmentID: "${envId}",${
  Constants.isCustomFlagsmithUrl()
    ? `\n      api: "${Constants.getFlagsmithSDKUrl()}",`
    : ''
}
  });
  return { flagsmithState: flagsmith.getState() }
}

// pages/index.js
import flagsmith from '@flagsmith/flagsmith/isomorphic';
import { useFlags, useFlagsmith } from '@flagsmith/flagsmith/react';

export default function HomePage() {
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
}`
