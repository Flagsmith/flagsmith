import Constants from 'common/constants'

export default (
  envId,
  { FEATURE_NAME, FEATURE_NAME_ALT, LIB_NAME, NPM_CLIENT },
) => `import ${LIB_NAME} from "${NPM_CLIENT}";
import { FlagsmithProvider, useFlags } from '${NPM_CLIENT}/react';

export function HomePage() {
  const flags = useFlags(['${FEATURE_NAME}','${FEATURE_NAME_ALT}']); // only causes re-render if specified flag values / traits change
  const ${FEATURE_NAME} = flags.${FEATURE_NAME}.enabled
  const ${FEATURE_NAME_ALT} = flags.${FEATURE_NAME_ALT}.value
  return (
    <>
      {\`${FEATURE_NAME}: \${${FEATURE_NAME}}\`}
      {\`${FEATURE_NAME_ALT}: \${${FEATURE_NAME_ALT}}\`}
    </>
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
