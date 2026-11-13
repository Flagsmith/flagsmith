const FALLBACK_ENVIRONMENT_NAMES = ['Development', 'Production']

// The default_environment_names_for_new_project flag value is a JSON array of names
export function getDefaultEnvironmentNames(flagValue: unknown): string[] {
  if (typeof flagValue !== 'string') {
    return FALLBACK_ENVIRONMENT_NAMES
  }
  try {
    const names: unknown = JSON.parse(flagValue)
    if (
      Array.isArray(names) &&
      names.length > 0 &&
      names.every((name) => typeof name === 'string' && name.trim())
    ) {
      return names
    }
  } catch {
    // An invalid flag value falls back rather than blocking project creation
  }
  return FALLBACK_ENVIRONMENT_NAMES
}
