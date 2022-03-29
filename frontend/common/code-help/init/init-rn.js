module.exports = (envId, { LIB_NAME, FEATURE_NAME, FEATURE_FUNCTION,NPM_RN_CLIENT, FEATURE_NAME_ALT, FEATURE_NAME_ALT_VALUE, NPM_CLIENT }, customFeature) => `// App root
import ${LIB_NAME} from "${NPM_RN_CLIENT}";
import { FlagsmithProvider } from 'flagsmith/react';
import AsyncStorage from '@react-native-async-storage/async-storage';

export default function App() {
  return (
    &lt;FlagsmithProvider
      options={{
        environmentID: '${envId}',
        cacheFlags: true,
        AsyncStorage: AsyncStorage, // Pass in whatever storage you use if you wish to cache flag values
      }}
      flagsmith={flagsmith}&gt;
      {...Your app}
    &lt;/FlagsmithProvider>
  );
}

// Home Page
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
