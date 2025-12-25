import moment from 'moment'

type Person = {
  firstName?: string
  lastName?: string
  email?: string
}

const Format = {
  age(value: string | null | undefined): number | string | null | undefined {
    // DATE > 10
    if (value) {
      const a = moment()
      const b = moment(value)
      return a.diff(b, 'years')
    }
    return value
  },

  ago(value: string | null | undefined): string | null | undefined {
    // DATE > 5 minutes ago (see moment docs)
    if (value) {
      const m = moment(value)
      return m.fromNow()
    }
    return value
  },

  camelCase(val: string): string {
    // hello world > Hello world
    return val.charAt(0).toUpperCase() + val.slice(1).toLowerCase()
  },

  countdown(value: string | null | undefined): string | null | undefined {
    // DATE > NOW || 10d1h10m
    let duration
    if (value) {
      if (Utils.isInPast(value)) {
        return 'Now'
      }
      duration = moment.duration({ from: moment(), to: moment(value) })
      return `${Format.nearestTen(
        Math.floor(duration.asDays()),
      )}d ${Format.nearestTen(duration.hours())}h ${Format.nearestTen(
        duration.minutes(),
      )}m`
    }
    return value
  },

  countdownMinutes(
    value: string | null | undefined,
  ): string | null | undefined {
    // DATE > 10:05
    let duration
    if (value) {
      duration = moment.duration({ from: moment(), to: moment(value) })
      return `${Format.nearestTen(duration.minutes())}:${Format.nearestTen(
        duration.seconds(),
      )}`
    }
    return value
  },

  cssImage(value: string | null | undefined): string {
    // lol.jpg  > url('lol.jpg')
    return value ? `url("${value}")` : 'none'
  },

  dateAndTime(value: string | null | undefined): string | null | undefined {
    return Format.moment(value, 'MMMM Do YYYY, h:mm a')
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

  initialAndLastName(person: Person | null | undefined): string {
    // {firstName:'Kyle', lastName:'Johnson'} > K. Johnson
    const value = Format.fullName(person)

    if (!value) {
      return value
    }

    const words = value.split(' ')

    if (words.length > 1) {
      return `${words[0].charAt(0).toUpperCase()}. ${words[words.length - 1]}`
    }

    return value
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

  money(
    value: number | null | undefined,
    defaultValue?: string | null,
  ): string | null | undefined {
    if (value === null || value === undefined || value === 0) {
      return defaultValue == null ? 'FREE' : defaultValue
    }

    return `£${value
      .toFixed(2)
      .replace(/./g, (c, i, a) =>
        i && c !== '.' && (a.length - i) % 3 === 0 ? `,${c}` : c,
      )}`
  },

  monthAndYear(value: string | null | undefined): string | null | undefined {
    return Format.moment(value, 'MMM YYYY')
  },

  nearestTen(value: number): string | number {
    // 11 > 10
    return value >= 10 ? value : `0${value}`
  },

  newLineDelimiter: '↵',

  ordinal(value: number | null | undefined): string {
    const s = ['th', 'st', 'nd', 'rd']
    const v = (value || 0) % 100
    return value ? value + (s[(v - 20) % 10] || s[v] || s[0]) : ''
  },

  removeAccents(str: string | null | undefined): string | null | undefined {
    // Sergio Agüero > Sergio Aguero
    if (!str) {
      return str
    }

    let result = str
    for (let i = 0; i < Utils.accents.length; i++) {
      result = result.replace(Utils.accents[i].letters, Utils.accents[i].base)
    }

    return result
  },

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

  time(value: string | null | undefined): string | null | undefined {
    // DATE > 10:00pm
    return Format.moment(value, 'hh:mm a')
  },

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
