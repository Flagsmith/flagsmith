export type EnvironmentSelection = string[] | string | null | undefined

type SelectionOptions = {
  multiple: boolean
  allowEmpty: boolean
}

// In single mode, clicking the picked one clears it only with allowEmpty.
export const getNextEnvironmentSelection = (
  value: EnvironmentSelection,
  clicked: string,
  { allowEmpty, multiple }: SelectionOptions,
): string[] | string | undefined => {
  if (multiple) {
    const current = Array.isArray(value) ? value : []
    return current.includes(clicked)
      ? current.filter((v) => v !== clicked)
      : [...current, clicked]
  }
  if (value !== clicked) return clicked
  return allowEmpty ? undefined : clicked
}
