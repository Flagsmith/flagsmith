export enum RuleContextLabels {
  IDENTIFIER = 'Identifier',
  ENVIRONMENT_NAME = 'Environment Name',
  IDENTITY_KEY = 'Identity Key',
}

export enum RuleContextValues {
  IDENTIFIER = '$.identity.identifier',
  IDENTITY_KEY = '$.identity.key',
  ENVIRONMENT_NAME = '$.environment.name',
}
