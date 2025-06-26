export enum FlagsmithStartupErrors {
  FOF_INIT_ERROR = 'fof_init_error',
  UNKNOWN_ERROR = 'unknown_error',
  MAINTENANCE_MODE = 'maintenance_mode',
}

const errorLabels: Record<FlagsmithStartupErrors, string> = {
  [FlagsmithStartupErrors.FOF_INIT_ERROR]:
    'Flagsmith on Flagsmith initialisation error. Please check your configuration',
  [FlagsmithStartupErrors.MAINTENANCE_MODE]: 'Maintenance mode',
  [FlagsmithStartupErrors.UNKNOWN_ERROR]:
    'Unexpected error. If it persists, please contact support',
}

export const getStartupErrorText = (error: FlagsmithStartupErrors) => {
  return errorLabels[error] || errorLabels[FlagsmithStartupErrors.UNKNOWN_ERROR]
}

export const isMaintenanceError = (error: FlagsmithStartupErrors) => {
  return error === FlagsmithStartupErrors.MAINTENANCE_MODE
}

export const isFlagsmithOnFlagsmithError = (error: FlagsmithStartupErrors) => {
  return error === FlagsmithStartupErrors.FOF_INIT_ERROR
}
