/**
 * Technical configuration constants for the application.
 *
 * This file contains runtime configuration values that affect application behavior,
 * as opposed to UI constants (colors, labels, etc.) which belong in constants.ts.
 */

export const config = {
  /**
   * Number of features to display per page in the features list.
   */
  FEATURES_PAGE_SIZE: 50,
} as const

export type Config = typeof config
