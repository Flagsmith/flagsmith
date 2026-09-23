import Constants from 'common/constants'

// baseURI belongs to FlagsmithConfig; FlagsmithClient itself only takes
// `apiKey` (plus optional config, seeds and storage).
export default (
  envId,
  { FEATURE_NAME, FEATURE_NAME_ALT },
) => `import 'package:flagsmith/flagsmith.dart';

final flagsmithClient = FlagsmithClient(
  apiKey: '${envId}',${
  Constants.isCustomFlagsmithUrl()
    ? `\n  config: FlagsmithConfig(baseURI: '${Constants.getFlagsmithSDKUrl()}'),`
    : ''
}
);

// The method below triggers a network request
await flagsmithClient.getFeatureFlags();

// Check whether the feature is enabled, or read its value
final isEnabled = await flagsmithClient.hasFeatureFlag('${FEATURE_NAME}');
final featureValue = await flagsmithClient.getFeatureFlagValue('${
  FEATURE_NAME_ALT || FEATURE_NAME
}');

print('${FEATURE_NAME} enabled: $isEnabled');
print('${FEATURE_NAME_ALT || FEATURE_NAME} value: $featureValue');
`
