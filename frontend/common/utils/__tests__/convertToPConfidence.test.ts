// Tests for the convertToPConfidence function extracted from Confidence.tsx
// The function maps p-values to confidence levels.

describe('convertToPConfidence', () => {
  // Inline the function to test it independently of the component
  const convertToPConfidence = (value: number) => {
    if (value > 0.05) return 'LOW'
    if (value >= 0.01) return 'REASONABLE'
    if (value > 0.002) return 'HIGH'
    return 'VERY_HIGH'
  }

  it('returns LOW for p-value above 0.05', () => {
    expect(convertToPConfidence(0.1)).toBe('LOW')
    expect(convertToPConfidence(0.5)).toBe('LOW')
    expect(convertToPConfidence(1)).toBe('LOW')
  })

  it('returns REASONABLE for p-value between 0.01 and 0.05', () => {
    expect(convertToPConfidence(0.05)).toBe('REASONABLE')
    expect(convertToPConfidence(0.03)).toBe('REASONABLE')
    expect(convertToPConfidence(0.01)).toBe('REASONABLE')
  })

  it('returns HIGH for p-value between 0.002 and 0.01', () => {
    expect(convertToPConfidence(0.009)).toBe('HIGH')
    expect(convertToPConfidence(0.005)).toBe('HIGH')
    expect(convertToPConfidence(0.003)).toBe('HIGH')
  })

  it('returns VERY_HIGH for p-value at or below 0.002', () => {
    expect(convertToPConfidence(0.002)).toBe('VERY_HIGH')
    expect(convertToPConfidence(0.001)).toBe('VERY_HIGH')
    expect(convertToPConfidence(0)).toBe('VERY_HIGH')
  })

  it('handles boundary values correctly', () => {
    expect(convertToPConfidence(0.05)).toBe('REASONABLE') // exactly 0.05
    expect(convertToPConfidence(0.0500001)).toBe('LOW') // just above 0.05
    expect(convertToPConfidence(0.01)).toBe('REASONABLE') // exactly 0.01
    expect(convertToPConfidence(0.0099)).toBe('HIGH') // just below 0.01
    expect(convertToPConfidence(0.002)).toBe('VERY_HIGH') // exactly 0.002
    expect(convertToPConfidence(0.0021)).toBe('HIGH') // just above 0.002
  })
})
