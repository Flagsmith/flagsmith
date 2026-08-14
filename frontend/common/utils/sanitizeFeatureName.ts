// Normalise a feature/flag name the way the backend expects: spaces become
// underscores, and the name is lower-cased when the project enforces lower-case
// feature names (only_allow_lower_case_feature_names). The backend regex stays
// the final word on validity.
export const sanitizeFeatureName = (
  raw: string,
  caseSensitive: boolean,
): string => {
  const next = raw.replace(/ /g, '_')
  return caseSensitive ? next.toLowerCase() : next
}

export default sanitizeFeatureName
