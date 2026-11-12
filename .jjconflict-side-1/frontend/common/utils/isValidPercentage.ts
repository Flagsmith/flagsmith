const isValidPercentage = (v: number): boolean =>
  v >= 0 && v <= 100 && !isNaN(v)

export default isValidPercentage
