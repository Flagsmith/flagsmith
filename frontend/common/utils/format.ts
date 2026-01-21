import moment from 'moment'

type Person = {
  firstName?: string
  lastName?: string
  email?: string
}

const Format = {
  camelCase(val: string): string {
    // hello world > Hello world
    return val.charAt(0).toUpperCase() + val.slice(1).toLowerCase()
  },

  enumeration: {
    get(value: string | null | undefined): string {
      // MY_CONSTANT > My constant
      if (!value) {
        return ''
      }
      return Format.camelCase(value.replace(/_/g, ' '))
    },
    set(value: string): string {
      // My Constant > MY_CONSTANT
      return value.replace(/ /g, '_').toUpperCase()
    },
  },

  fullName(person: Person | null | undefined): string {
    // {firstName:'Kyle', lastName:'Johnson'} > Kyle Johnson
    if (!person) {
      return ''
    }
    const fn = person.firstName || ''
    const sn = person.lastName || ''

    return fn
      ? `${Format.camelCase(fn)} ${Format.camelCase(sn)}`
      : Format.camelCase(sn)
  },

  moment(
    value: string | null | undefined,
    format: string,
  ): string | null | undefined {
    // DATE, hh:mm > 23:00
    if (value) {
      const m = moment(value)
      return m.format(format)
    }
    return value
  },

  nearestTen(value: number): string | number {
    // 11 > 10
    return value >= 10 ? value : `0${value}`
  },

  newLineDelimiter: '↵',

  shortenNumber(number: number): string {
    // Converts a float number into a short literal with suffix for the magnitude:
    // 1523125 > 1.5M
    const suffixes = ['', 'K', 'M', 'B', 'T']
    const numDigits = Math.floor(Math.log10(number)) + 1
    const suffixIndex = Math.floor((numDigits - 1) / 3)

    let shortValue: number = number / Math.pow(1000, suffixIndex)
    shortValue = +shortValue.toFixed(1)

    return shortValue + suffixes[suffixIndex]
  },

  spaceDelimiter: '␣',
  tabDelimiter: '[TAB]',

  trimAndHighlightSpaces(
    string: string | null | undefined,
  ): string | undefined {
    return string
      ?.replace?.(/(^\s+|\s+$)/gm, Format.spaceDelimiter)
      ?.replace(/\t/g, Format.tabDelimiter)
      ?.replace(/(\r)/g, Format.newLineDelimiter)
      ?.replace(/(\n)/g, Format.newLineDelimiter)
  },

  truncateText(
    text: string | null | undefined,
    numberOfChars: number,
  ): string | null | undefined {
    // lol,1 > l...
    if (text) {
      if (text.length > numberOfChars) {
        return `${text.substring(0, numberOfChars)}...`
      }
    }
    return text
  },

  userDisplayName(person: Person & { email: string }): string {
    // {firstName:'John', lastName:'Doe', email: 'JD123@email.com'} > John Doe || JD123@email.com
    return Format.fullName(person) || person.email
  },
}

export default Format
