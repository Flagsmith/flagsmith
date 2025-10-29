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

export type OperatorValue =
  | 'EQUAL'
  | 'NOT_EQUAL'
  | 'PERCENTAGE_SPLIT'
  | 'GREATER'
  | 'LESS'
  | 'IS_SET'
  | 'IS_NOT_SET'
  | 'CONTAINS'
  | 'NOT_CONTAINS'
  | 'REGEX'
  | 'MODULO'
  | 'IN'
