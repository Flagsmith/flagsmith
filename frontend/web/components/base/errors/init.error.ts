export enum FlagsmithStartupErrors {
  FOF_INIT_ERROR = 'fof_init_error',
  UNKNOWN_ERROR = 'unknown_error',
  MAINTENANCE_MODE = 'maintenance_mode',
}

export interface SDKInitErrors {
  type: FlagsmithStartupErrors
  message: string
}

const errorLabels: Record<FlagsmithStartupErrors, string> = {
  [FlagsmithStartupErrors.FOF_INIT_ERROR]:
    'Please check your Flagsmith configuration',
  [FlagsmithStartupErrors.MAINTENANCE_MODE]: 'Maintenance mode',
  [FlagsmithStartupErrors.UNKNOWN_ERROR]:
    'Unexpected error. If it persists, please contact support',
}

export const getStartupErrorText = (error: SDKInitErrors) => {
  switch (error?.type) {
    case FlagsmithStartupErrors.FOF_INIT_ERROR:
      return `${error?.message}. ${errorLabels[error?.type]}`
    case FlagsmithStartupErrors.MAINTENANCE_MODE:
      return errorLabels[error?.type]
    default:
      return errorLabels[FlagsmithStartupErrors.UNKNOWN_ERROR]
  }
}

export const isMaintenanceError = (error: SDKInitErrors) => {
  return error?.type === FlagsmithStartupErrors.MAINTENANCE_MODE
}

export const isFlagsmithOnFlagsmithError = (error: SDKInitErrors) => {
  return error?.type === FlagsmithStartupErrors.FOF_INIT_ERROR
}
