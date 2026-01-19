import Format from 'common/utils/format'

describe('Format', () => {
  describe('shortenNumber', () => {
    it.each`
      input            | expected
      ${1523125}       | ${'1.5M'}
      ${1500}          | ${'1.5K'}
      ${1500000000}    | ${'1.5B'}
      ${1500000000000} | ${'1.5T'}
      ${1000}          | ${'1K'}
      ${1234}          | ${'1.2K'}
      ${12345}         | ${'12.3K'}
      ${123456}        | ${'123.5K'}
    `('shortenNumber($input) returns $expected', ({ expected, input }) => {
      expect(Format.shortenNumber(input)).toBe(expected)
    })
  })

  describe('nearestTen', () => {
    it.each`
      input | expected
      ${0}  | ${'00'}
      ${5}  | ${'05'}
      ${9}  | ${'09'}
      ${10} | ${10}
      ${15} | ${15}
      ${99} | ${99}
    `('nearestTen($input) returns $expected', ({ expected, input }) => {
      expect(Format.nearestTen(input)).toBe(expected)
    })
  })

  describe('camelCase', () => {
    it.each`
      input            | expected
      ${'hello'}       | ${'Hello'}
      ${'HELLO'}       | ${'Hello'}
      ${'hELLO'}       | ${'Hello'}
      ${'a'}           | ${'A'}
      ${'hello world'} | ${'Hello world'}
    `('camelCase("$input") returns "$expected"', ({ expected, input }) => {
      expect(Format.camelCase(input)).toBe(expected)
    })
  })

  describe('enumeration', () => {
    describe('get', () => {
      it.each`
        input            | expected
        ${'MY_CONSTANT'} | ${'My constant'}
        ${'HELLO_WORLD'} | ${'Hello world'}
        ${'CONSTANT'}    | ${'Constant'}
        ${null}          | ${''}
        ${undefined}     | ${''}
      `(
        'enumeration.get($input) returns "$expected"',
        ({ expected, input }) => {
          expect(Format.enumeration.get(input)).toBe(expected)
        },
      )
    })

    describe('set', () => {
      it.each`
        input            | expected
        ${'My Constant'} | ${'MY_CONSTANT'}
        ${'Hello World'} | ${'HELLO_WORLD'}
      `(
        'enumeration.set("$input") returns "$expected"',
        ({ expected, input }) => {
          expect(Format.enumeration.set(input)).toBe(expected)
        },
      )
    })
  })

  describe('fullName', () => {
    it.each`
      person                                        | expected
      ${{ firstName: 'kyle', lastName: 'johnson' }} | ${'Kyle Johnson'}
      ${{ firstName: 'KYLE', lastName: 'JOHNSON' }} | ${'Kyle Johnson'}
      ${{ lastName: 'johnson' }}                    | ${'Johnson'}
      ${{ firstName: 'kyle' }}                      | ${'Kyle '}
      ${null}                                       | ${''}
      ${undefined}                                  | ${''}
      ${{}}                                         | ${''}
    `('fullName($person) returns "$expected"', ({ expected, person }) => {
      expect(Format.fullName(person)).toBe(expected)
    })
  })

  describe('initialAndLastName', () => {
    it.each`
      person                                        | expected
      ${{ firstName: 'kyle', lastName: 'johnson' }} | ${'K. Johnson'}
      ${{ lastName: 'johnson' }}                    | ${'Johnson'}
      ${null}                                       | ${''}
      ${undefined}                                  | ${''}
    `(
      'initialAndLastName($person) returns "$expected"',
      ({ expected, person }) => {
        expect(Format.initialAndLastName(person)).toBe(expected)
      },
    )
  })

  describe('truncateText', () => {
    it.each`
      text             | length | expected
      ${'hello world'} | ${5}   | ${'hello...'}
      ${'hello'}       | ${10}  | ${'hello'}
      ${'hello'}       | ${5}   | ${'hello'}
      ${null}          | ${5}   | ${null}
      ${undefined}     | ${5}   | ${undefined}
    `(
      'truncateText("$text", $length) returns $expected',
      ({ expected, length, text }) => {
        expect(Format.truncateText(text, length)).toBe(expected)
      },
    )
  })

  describe('ordinal', () => {
    it.each`
      input        | expected
      ${1}         | ${'1st'}
      ${2}         | ${'2nd'}
      ${3}         | ${'3rd'}
      ${4}         | ${'4th'}
      ${11}        | ${'11th'}
      ${12}        | ${'12th'}
      ${13}        | ${'13th'}
      ${21}        | ${'21st'}
      ${22}        | ${'22nd'}
      ${23}        | ${'23rd'}
      ${24}        | ${'24th'}
      ${null}      | ${''}
      ${undefined} | ${''}
      ${0}         | ${''}
    `('ordinal($input) returns "$expected"', ({ expected, input }) => {
      expect(Format.ordinal(input)).toBe(expected)
    })
  })

  describe('money', () => {
    it.each`
      value        | defaultVal   | expected
      ${10}        | ${undefined} | ${'£10.00'}
      ${10.5}      | ${undefined} | ${'£10.50'}
      ${1000}      | ${undefined} | ${'£1,000.00'}
      ${1000000}   | ${undefined} | ${'£1,000,000.00'}
      ${0}         | ${undefined} | ${'FREE'}
      ${0}         | ${'N/A'}     | ${'N/A'}
      ${null}      | ${undefined} | ${'FREE'}
      ${null}      | ${'N/A'}     | ${'N/A'}
      ${undefined} | ${undefined} | ${'FREE'}
      ${undefined} | ${'N/A'}     | ${'N/A'}
    `(
      'money($value, $defaultVal) returns "$expected"',
      ({ defaultVal, expected, value }) => {
        expect(Format.money(value, defaultVal)).toBe(expected)
      },
    )
  })

  describe('cssImage', () => {
    it.each`
      value          | expected
      ${'image.jpg'} | ${'url("image.jpg")'}
      ${null}        | ${'none'}
      ${undefined}   | ${'none'}
    `('cssImage($value) returns "$expected"', ({ expected, value }) => {
      expect(Format.cssImage(value)).toBe(expected)
    })
  })

  describe('trimAndHighlightSpaces', () => {
    it.each`
      value             | expected
      ${'  hello  '}    | ${'␣hello␣'}
      ${'hello\tworld'} | ${'hello[TAB]world'}
      ${'hello\nworld'} | ${'hello↵world'}
      ${null}           | ${undefined}
      ${undefined}      | ${undefined}
    `(
      'trimAndHighlightSpaces($value) returns $expected',
      ({ expected, value }) => {
        expect(Format.trimAndHighlightSpaces(value)).toBe(expected)
      },
    )
  })

  describe('userDisplayName', () => {
    it.each`
      user                                                               | expected
      ${{ email: 'john@email.com', firstName: 'John', lastName: 'Doe' }} | ${'John Doe'}
      ${{ email: 'john@email.com' }}                                     | ${'john@email.com'}
    `('userDisplayName($user) returns "$expected"', ({ expected, user }) => {
      expect(Format.userDisplayName(user)).toBe(expected)
    })
  })

  describe('removeAccents', () => {
    it.each`
      input         | expected
      ${'Café'}     | ${'Cafe'}
      ${'naïve'}    | ${'naive'}
      ${'Müller'}   | ${'Muller'}
      ${'Agüero'}   | ${'Aguero'}
      ${'résumé'}   | ${'resume'}
      ${'Ångström'} | ${'Angstrom'}
      ${'Señor'}    | ${'Senor'}
      ${'Łódź'}     | ${'Lodz'}
      ${'hello'}    | ${'hello'}
      ${'HELLO'}    | ${'HELLO'}
      ${null}       | ${null}
      ${undefined}  | ${undefined}
    `('removeAccents("$input") returns "$expected"', ({ expected, input }) => {
      expect(Format.removeAccents(input)).toBe(expected)
    })
  })

  /*
   * ============================================================================
   * UNTESTED FUNCTIONS
   * ============================================================================
   *
   * Date/time wrappers (moment, dateAndTime, monthAndYear, time):
   * - These are thin wrappers around moment.js - testing them would just test
   *   the third-party library, not our code.
   *
   * Time-relative functions (age, ago, countdown, countdownMinutes):
   * - Use moment() to get current time, making output non-deterministic
   * - Would need dependency injection (Clock pattern) to test properly
   * ============================================================================
   */
})
