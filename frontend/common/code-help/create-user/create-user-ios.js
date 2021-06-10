import Utils from '../../utils/utils';

module.exports = (envId, { FEATURE_NAME,USER_ID, FEATURE_FUNCTION, FEATURE_NAME_ALT }) => `import BulletTrainClient

func application(_ application: UIApplication,
 didFinishLaunchingWithOptions launchOptions:
  [UIApplication.LaunchOptionsKey: Any]?) -> Bool {

  BulletTrain.shared.apiKey = "${envId}"
  
  // This will create a user in the dashboard if they don't already exist
  
  // Check for a feature
  BulletTrain.shared
  .hasFeatureFlag(withID: "${FEATURE_NAME}", forIdentity: "${USER_ID}") { (result) in
      print(result)
  }

  // Or, use the value of a feature
  BulletTrain.shared
  .getFeatureValue(withID: "${FEATURE_NAME_ALT}", forIdentity: "${USER_ID}") { (result) in
      switch result {
      case .success(let value):
          print(value ?? "nil")
      case .failure(let error):
          print(error)
      }
  }
}`;
