import Utils from '../../utils/utils';

module.exports = (envId, { FEATURE_NAME, FEATURE_FUNCTION, USER_ID, FEATURE_NAME_ALT }) => `let bt = bullettrain::Client::new("${envId}");

fn test_user() -> User {
    User {
        identifier: String::from("${USER_ID}"),
    }
}
...

let hasFeature = client.has_user_feature(&test_user(), "${FEATURE_NAME}").unwrap();
let featureValue = client.get_user_value(&test_user(), "${FEATURE_NAME_ALT}")
        .unwrap()
        .unwrap();
`;
