module.exports = (envId, { NPM_RN_CLIENT, TRAIT_NAME, NPM_CLIENT, USER_ID, USER_FEATURE_FUNCTION, FEATURE_NAME, FEATURE_NAME_ALT }, userId) => `
// Home Page
import flagsmith from '${NPM_RN_CLIENT}';
import { useFlags, useFlagsmith } from 'flagsmith/react';

export default function HomePage() {
  const flags = useFlags(['${FEATURE_NAME}','${FEATURE_NAME_ALT}']]); // only causes re-render if specified flag values / traits change
  const ${FEATURE_NAME} = flags.${FEATURE_NAME}.enabled
  const ${FEATURE_NAME_ALT} = flags.${FEATURE_NAME_ALT}.value
  
  const identify = () => {
    flagsmith.identify('${USER_ID}', {${TRAIT_NAME}: 21}); // only causes re-render if the user has overrides / segment overrides for ${FEATURE_NAME} or ${FEATURE_NAME_ALT}
  };
  
  return (
    &lt;>{...}&lt;/>
  );
}`;
