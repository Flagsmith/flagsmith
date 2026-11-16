export type Rgb = { r: number; g: number; b: number }

export const parseHex = (hex: string): Rgb | null => {
  const match = /^#?([0-9a-f]{6})$/i.exec(hex.trim())
  if (!match) return null
  const n = parseInt(match[1], 16)
  return { b: n & 255, g: (n >> 8) & 255, r: (n >> 16) & 255 }
}
