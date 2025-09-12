import Constants from 'common/constants'

module.exports = (
  envId,
  { FEATURE_NAME, FEATURE_NAME_ALT },
) => `import FlagsmithClient

func application(_ application: UIApplication,
 didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?) -> Bool {

  Flagsmith.shared.apiKey = "${envId}"${
  Constants.isCustomFlagsmithUrl() &&
  `\n  Flagsmith.shared.baseURL = "${Constants.getFlagsmithSDKUrl()}"\n`
}
  // Check for a feature
  Flagsmith.shared
  .hasFeatureFlag(withID: "${FEATURE_NAME}", forIdentity: nil) { (result) in
      print(result)
  }

  // Or, use the value of a feature
  Flagsmith.shared
  .getFeatureValue(withID: "${FEATURE_NAME_ALT}", forIdentity: nil) { (result) in
      switch result {
      case .success(let value):
          print(value ?? "nil")
      case .failure(let error):
          print(error)
      }
  }
}`
