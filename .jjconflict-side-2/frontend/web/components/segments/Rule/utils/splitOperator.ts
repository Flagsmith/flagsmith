export const splitIfValue = (v: string | null | number, append: string) =>
  append && typeof v === 'string' ? v.split(append) : [v === null ? '' : v]

export const isInvalidPercentageSplit = (value: string | boolean | number) =>
  `${value}`?.match(/\D/) || (parseInt(value?.toString() || '0') as any) > 100
