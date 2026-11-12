// A 6-digit hex colour as #RRGGBB, with or without the # given; null otherwise.
export const toHexColour = (value: string | null | undefined) => {
  const match = /^#?([0-9a-f]{6})$/i.exec(value?.trim() ?? '')
  return match ? `#${match[1]}` : null
}
