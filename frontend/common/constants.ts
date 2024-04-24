import { OAuthType } from './types/requests'
import { SegmentCondition } from './types/responses'

const keywords = {
  FEATURE_FUNCTION: 'myCoolFeature',
  FEATURE_NAME: 'my_cool_feature',
  FEATURE_NAME_ALT: 'banner_size',
  FEATURE_NAME_ALT_VALUE: 'big',
  LIB_NAME: 'flagsmith',
  LIB_NAME_JAVA: 'FlagsmithClient',
  NPM_CLIENT: 'flagsmith',
  NPM_NODE_CLIENT: 'flagsmith-nodejs',
  SEGMENT_NAME: 'superUsers',
  TRAIT_NAME: 'age',
  URL_CLIENT: 'https://cdn.jsdelivr.net/npm/flagsmith/index.js',
  USER_FEATURE_FUNCTION: 'myEvenCoolerFeature',
  USER_FEATURE_NAME: 'my_even_cooler_feature',
  USER_ID: 'user_123456',
}
const keywordsReactNative = {
  ...keywords,
  NPM_CLIENT: 'react-native-flagsmith',
}
export default {
  archivedTag: { color: '#8f8f8f', label: 'Archived' },
  codeHelp: {
    'CREATE_USER': (envId: string, userId: string = keywords.USER_ID) => ({
      '.NET': require('./code-help/create-user/create-user-dotnet')(
        envId,
        keywords,
        userId,
      ),
      'Flutter': require('./code-help/create-user/create-user-flutter')(
        envId,
        keywords,
        userId,
      ),
      'Go': require('./code-help/create-user/create-user-go')(
        envId,
        keywords,
        userId,
      ),
      'Java': require('./code-help/create-user/create-user-java')(
        envId,
        keywords,
        userId,
      ),
      'JavaScript': require('./code-help/create-user/create-user-js')(
        envId,
        keywords,
        userId,
      ),
      'Next.js': require('./code-help/create-user/create-user-next')(
        envId,
        keywords,
        userId,
      ),
      'Node JS': require('./code-help/create-user/create-user-node')(
        envId,
        keywords,
        userId,
      ),
      'PHP': require('./code-help/create-user/create-user-php')(
        envId,
        keywords,
        userId,
      ),
      'Python': require('./code-help/create-user/create-user-python')(
        envId,
        keywords,
        userId,
      ),
      'React': require('./code-help/create-user/create-user-react')(
        envId,
        keywords,
        userId,
      ),
      'React Native': require('./code-help/create-user/create-user-react')(
        envId,
        keywordsReactNative,
        userId,
      ),
      'Ruby': require('./code-help/create-user/create-user-ruby')(
        envId,
        keywords,
        userId,
      ),
      'Rust': require('./code-help/create-user/create-user-rust')(
        envId,
        keywords,
        userId,
      ),
      'curl': require('./code-help/create-user/create-user-curl')(
        envId,
        keywords,
        userId,
      ),
      'iOS': require('./code-help/create-user/create-user-ios')(
        envId,
        keywords,
        userId,
      ),
    }),

    'INIT': (envId: string) => ({
      '.NET': require('./code-help/init/init-dotnet')(envId, keywords),
      'Flutter': require('./code-help/init/init-flutter')(envId, keywords),
      'Go': require('./code-help/init/init-go')(envId, keywords),
      'Java': require('./code-help/init/init-java')(envId, keywords),
      'JavaScript': require('./code-help/init/init-js')(envId, keywords),
      'Next.js': require('./code-help/init/init-next')(envId, keywords),
      'Node JS': require('./code-help/init/init-node')(envId, keywords),
      'PHP': require('./code-help/init/init-php')(envId, keywords),
      'Python': require('./code-help/init/init-python')(envId, keywords),
      'React': require('./code-help/init/init-react')(envId, keywords),
      'React Native': require('./code-help/init/init-js')(
        envId,
        keywordsReactNative,
      ),
      'Ruby': require('./code-help/init/init-ruby')(envId, keywords),
      'Rust': require('./code-help/init/init-rust')(envId, keywords),
      'curl': require('./code-help/init/init-curl')(envId, keywords),
      'iOS': require('./code-help/init/init-ios')(envId, keywords),
    }),

    'INSTALL': {
      '.NET': require('./code-help/install/install-dotnet')(keywords),
      'Flutter': require('./code-help/install/install-flutter')(keywords),
      'Go': require('./code-help/install/install-go')(keywords),
      'Java': require('./code-help/install/install-java')(keywords),
      'JavaScript': require('./code-help/install/install-js')(keywords),
      'Next.js': require('./code-help/install/install-js')(keywords),
      'Node JS': require('./code-help/install/install-node')(keywords),
      'PHP': require('./code-help/install/install-php')(keywords),
      'Python': require('./code-help/install/install-python')(keywords),
      'React': require('./code-help/install/install-js')(keywords),
      'React Native': require('./code-help/install/install-js')(
        keywordsReactNative,
      ),
      'Ruby': require('./code-help/install/install-ruby')(keywords),
      'Rust': require('./code-help/install/install-rust')(keywords),
      'curl': require('./code-help/install/install-curl')(keywords),
      'iOS': require('./code-help/install/install-ios')(keywords),
    },

    'OFFLINE_LOCAL': (envId: string) => ({
      'cli': require('common/code-help/offline_server/offline-server-cli')(
        envId,
      ),
      'curl': require('common/code-help/offline_server/offline-server-curl')(
        envId,
      ),
    }),

    'OFFLINE_REMOTE': (envId: string) => ({
      'cli': require('common/code-help/offline_client/offline-client-cli')(
        envId,
        keywords,
      ),
      'curl': require('common/code-help/offline_client/offline-client-curl')(
        envId,
        keywords,
      ),
    }),

    'USER_TRAITS': (envId: string, userId?: string) => ({
      '.NET': require('./code-help/traits/traits-dotnet')(
        envId,
        keywords,
        userId,
      ),
      'Flutter': require('./code-help/traits/traits-flutter')(
        envId,
        keywords,
        userId,
      ),
      'Go': require('./code-help/traits/traits-go')(envId, keywords, userId),
      'Java': require('./code-help/traits/traits-java')(
        envId,
        keywords,
        userId,
      ),
      'JavaScript': require('./code-help/traits/traits-js')(
        envId,
        keywords,
        userId,
      ),
      'Next.js': require('./code-help/traits/traits-next')(
        envId,
        keywords,
        userId,
      ),
      'Node JS': require('./code-help/traits/traits-node')(
        envId,
        keywords,
        userId,
      ),
      'PHP': require('./code-help/traits/traits-php')(envId, keywords, userId),
      'Python': require('./code-help/traits/traits-python')(
        envId,
        keywords,
        userId,
      ),
      'React': require('./code-help/traits/traits-react')(
        envId,
        keywords,
        userId,
      ),
      'React Native': require('./code-help/traits/traits-react')(
        envId,
        keywordsReactNative,
        userId,
      ),
      'Ruby': require('./code-help/traits/traits-ruby')(
        envId,
        keywords,
        userId,
      ),
      'Rust': require('./code-help/traits/traits-rust')(
        envId,
        keywords,
        userId,
      ),
      'curl': require('./code-help/traits/traits-curl')(
        envId,
        keywords,
        userId,
      ),
      'iOS': require('./code-help/traits/traits-ios')(envId, keywords, userId),
    }),

    keys: {
      'Java': 'java',
      'JavaScript': 'javascript',
      'Node JS': 'javascript',
      'React Native': 'javascript',
    },
  },
  colours: {
    primary: '#6837fc',
    white: '#ffffff',
  },
  defaultRule: {
    operator: 'EQUAL',
    property: '',
    value: '',
  } as SegmentCondition,
  environmentPermissions: (perm: string) =>
    `To manage this feature you need the <i>${perm}</i> permission for this environment.<br/>Please contact a member of this environment who has administrator privileges.`,
  events: {
    'ACCEPT_INVITE': (org: any) => ({
      'category': 'Invite',
      'event': 'Invite accepted',
      extra: org,
    }),
    'CREATE_ENVIRONMENT': {
      'category': 'Environment',
      'event': 'Environment created',
    },
    'CREATE_FEATURE': { 'category': 'Features', 'event': 'Feature created' },
    'CREATE_FIRST_FEATURE': {
      'category': 'First',
      'event': 'First Feature created',
    },
    'CREATE_FIRST_ORGANISATION': {
      'category': 'First',
      'event': 'First Organisation created',
    },
    'CREATE_FIRST_PROJECT': {
      'category': 'First',
      'event': 'First Project created',
    },
    'CREATE_FIRST_SEGMENT': {
      'category': 'First',
      'event': 'First Segment created',
    },
    'CREATE_GROUP': { 'category': 'Group', 'event': 'Group created' },
    'CREATE_ORGANISATION': {
      'category': 'Organisation',
      'event': 'Organisation created',
    },
    'CREATE_PROJECT': { 'category': 'Project', 'event': 'Project created' },
    'CREATE_SEGMENT': { 'category': 'Segments', 'event': 'Segment created' },
    'CREATE_USER_FEATURE': {
      'category': 'User Features',
      'event': 'User feature created',
    },
    'DELETE_GROUP': { 'category': 'Group', 'event': 'Group deleted' },
    'DELETE_INVITE': { 'category': 'Invite', 'event': 'Invite deleted' },
    'DELETE_ORGANISATION': {
      'category': 'Organisation',
      'event': 'Organisation deleted',
    },
    'DELETE_USER': { 'category': 'Organisation', 'event': 'User deleted' },
    'EDIT_ENVIRONMENT': {
      'category': 'Environment',
      'event': 'Environment edited',
    },
    'EDIT_FEATURE': { 'category': 'Features', 'event': 'Feature edited' },
    'EDIT_ORGANISATION': {
      'category': 'Organisation',
      'event': 'Organisation edited',
    },
    'EDIT_PROJECT': { 'category': 'Project', 'event': 'Project edited' },
    'EDIT_USER_FEATURE': {
      'category': 'Features',
      'event': 'User feature edited',
    },
    'INVITE': { 'category': 'Invite', 'event': 'Invite sent' },
    'LOGIN': { 'category': 'User', 'event': 'User login' },
    'OAUTH': (type: OAuthType) => ({
      'category': 'User',
      'event': `User oauth ${type}`,
    }),
    'REFERRER_CONVERSION': (referrer: string) => ({
      'category': 'Referrer',
      'event': `${referrer} converted`,
    }),
    'REFERRER_REGISTERED': (referrer: string) => ({
      'category': 'Referrer',
      'event': `${referrer} registered`,
    }),
    'REGISTER': { 'category': 'User', 'event': 'User register' },
    'REMOVE_ENVIRONMENT': {
      'category': 'Environment',
      'event': 'Environment edited',
    },
    'REMOVE_FEATURE': { 'category': 'Features', 'event': 'Feature removed' },
    'REMOVE_PROJECT': { 'category': 'Project', 'event': 'Project removed' },
    'REMOVE_USER_FEATURE': {
      'category': 'User Features',
      'event': 'User feature removed',
    },
    'RESEND_INVITE': { 'category': 'Invite', 'event': 'Invite resent' },
    'TOGGLE_FEATURE': { 'category': 'Features', 'event': 'Feature toggled' },
    'TOGGLE_USER_FEATURE': {
      'category': 'User Features',
      'event': 'User feature toggled',
    },
    'TRY_IT': { 'category': 'TryIt', 'event': 'Try it clicked' },
    'UPDATE_USER_ROLE': {
      'category': 'Organisation',
      'event': 'Updated user role',
    },
    'VIEW_FEATURE': { 'category': 'Features', 'event': 'Feature viewed' },
    'VIEW_SEGMENT': { 'category': 'Segment', 'event': 'Segment viewed' },
    'VIEW_USER_FEATURE': {
      'category': 'User Features',
      'event': 'User feature viewed',
    },
  },
  exampleAuditWebhook: `{
 "created_date": "2020-02-23T17:30:57.006318Z",
 "log": "New Flag / Remote Config created: my_feature",
 "author": {
  "id": 3,
  "email": "user@domain.com",
  "first_name": "Kyle",
  "last_name": "Johnson"
 },
 "environment": null,
 "project": {
  "id": 6,
  "name": "Project name",
  "organisation": 1
 },
 "related_object_id": 6,
 "related_object_type": "FEATURE"
}`,
  exampleWebhook: `{
 "data": {
  "changed_by": "Ben Rometsch",
  "new_state": {
   "enabled": true,
   "environment": {
    "id": 23,
    "name": "Development"
   },
   "feature": {
    "created_date": "2021-02-10T20:03:43.348556Z",
    "default_enabled": false,
    "description": "Show html in a butter bar for certain users",
    "id": 7168,
    "initial_value": null,
    "name": "butter_bar",
    "project": {
     "id": 12,
     "name": "Flagsmith Website"
    },
    "type": "CONFIG"
   },
   "feature_segment": null,
   "feature_state_value": "<strong>\\nYou are using the develop environment.\\n</strong>",
   "identity": null,
   "identity_identifier": null
  },
  "previous_state": {
   "enabled": false,
   "environment": {
    "id": 23,
    "name": "Development"
   },
   "feature": {
    "created_date": "2021-02-10T20:03:43.348556Z",
    "default_enabled": false,
    "description": "Show html in a butter bar for certain users",
    "id": 7168,
    "initial_value": null,
    "name": "butter_bar",
    "project": {
     "id": 12,
     "name": "Flagsmith Website"
    },
    "type": "CONFIG"
   },
   "feature_segment": null,
   "feature_state_value": "<strong>\\nYou are using the develop environment.\\n</strong>",
   "identity": null,
   "identity_identifier": null
  },
  "timestamp": "2021-06-18T07:50:26.595298Z"
 },
 "event_type": "FLAG_UPDATED"
}`,
  forms: {
    maxLength: {
      'FEATURE_ID': 150,
      'SEGMENT_ID': 150,
      'TRAITS_ID': 150,
    },
  },
  modals: {
    'PAYMENT': 'Payment Modal',
  },
  organisationPermissions: (perm: string) =>
    `To manage this feature you need the <i>${perm}</i> permission for this organisastion.<br/>Please contact a member of this organisation who has administrator privileges.`,
  pages: {
    'ACCOUNT': 'Account Page',
    'AUDIT_LOG': 'Audit Log Page',
    'COMING_SOON': 'Coming Soon Page',
    'CREATE_ENVIRONMENT': 'Create Environment Page',
    'DOCUMENTATION': 'Documentation Page',
    'ENVIRONMENT_SETTINGS': 'Environment Settings Page',
    'FEATURES': 'Features Page',
    'HOME': 'Home Page',
    'INTEGRATIONS': 'Integrations Page',
    'INVITE': 'User Invited Page',
    'NOT_FOUND': '404 Page',
    'ORGANISATION_SETTINGS': 'Organisation Settings Page',
    'POLICIES': 'Terms & Policies Page',
    'PRICING': 'Pricing Page',
    'PROJECT_SELECT': 'Project Select Page',
    'PROJECT_SETTINGS': 'Project Settings Page',
    'RESET_PASSWORD': 'Reset Password Page',
    'USER': 'User Page',
    'USERS': 'Users Page',
    'WHAT_ARE_FEATURE_FLAGS': 'What are feature flags Page',
  },
  projectColors: [
    '#906AF6',
    '#FAE392',
    '#42D0EB',
    '#56CCAD',
    '#FFBE71',
    '#F57C78',
  ],
  projectPermissions: (perm: string) =>
    `To use this feature you need the <i>${perm}</i> permission for this project.<br/>Please contact a member of this project who has administrator privileges.`,
  roles: {
    'ADMIN': 'Organisation Administrator',
    'USER': 'User',
  },
  simulate: {},
  strings: {
    AUDIT_WEBHOOKS_DESCRIPTION:
      'Receive a webhook for when an audit log is received.',
    ENVIRONMENT_DESCRIPTION:
      'Environments are versions of your projects, environments within a project all share the same features but can be individually turned on/off or have different values.',
    ENVIRONMENT_OVERRIDE_DESCRIPTION: (name: string) =>
      `Features are created once per project<br/>but their <strong>value</strong> and <strong>enabled state</strong> are set per environment.<br/>Saving this feature will override the <strong>${name}</strong> environment.`,
    FEATURE_FLAG_DESCRIPTION:
      'A feature that you can turn on or off per environment or user, e.g. instant messaging for a mobile app or an endpoint for an API.',
    HIDE_FROM_SDKS_DESCRIPTION:
      "Enable this if you want to prevent the Flagsmith API from returning this feature regardless of if it is enabled. Use this if you don't want users to see that a feature name whilst it is in development.",
    IDENTITY_OVERRIDES_DESCRIPTION:
      'See which identities have specific overridden values for this feature.<br/>Identity overrides take priority over segment overrides and environment values.',
    ORGANISATION_DESCRIPTION:
      'This is used to create a default organisation for team members to create and manage projects.',
    REMOTE_CONFIG_DESCRIPTION:
      'Features can have values as well as being simply on or off, e.g. a font size for a banner or an environment variable for a server.',
    REMOTE_CONFIG_DESCRIPTION_VARIATION:
      'Features can have values as well as being simply on or off, e.g. a font size for a banner or an environment variable for a server.<br/>Variation values are set per project, the environment weight is per environment.',
    SEGMENT_OVERRIDES_DESCRIPTION:
      'Set different values for your feature based on what segments users are in. Identity overrides will take priority over any segment override.',
    TAGS_DESCRIPTION:
      'Organise your flags with tags, tagging your features as "<strong>protected</strong>" will prevent them from accidentally being deleted.',
    USER_PROPERTY_DESCRIPTION:
      'The name of the user trait or custom property belonging to the user, e.g. firstName',
    WEBHOOKS_DESCRIPTION:
      'Receive a webhook for when feature values are changed.',
  },
  tagColors: [
    '#3d4db6',
    '#ea5a45',
    '#c6b215',
    '#60bd4e',
    '#fe5505',
    '#1492f4',
    '#14c0f4',
    '#c277e0',
    '#039587',
    '#344562',
    '#ffa500',
    '#3cb371',
    '#d3d3d3',
    '#5D6D7E',
    '#641E16',
    '#5B2C6F',
    '#D35400',
    '#F08080',
    '#AAC200',
    '#DE3163',
  ],
  untaggedTag: { color: '#dedede', label: 'Untagged' },
}
