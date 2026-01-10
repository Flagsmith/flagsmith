import Format from 'common/utils/format'

describe('Format', () => {
  describe('shortenNumber', () => {
    it('should shorten millions with M suffix', () => {
      expect(Format.shortenNumber(1523125)).toBe('1.5M')
    })

    it('should shorten thousands with K suffix', () => {
      expect(Format.shortenNumber(1500)).toBe('1.5K')
    })

    it('should shorten billions with B suffix', () => {
      expect(Format.shortenNumber(1500000000)).toBe('1.5B')
    })

    it('should shorten trillions with T suffix', () => {
      expect(Format.shortenNumber(1500000000000)).toBe('1.5T')
    })

    it('should handle exact thousands', () => {
      expect(Format.shortenNumber(1000)).toBe('1K')
    })

    it('should handle numbers with decimal precision', () => {
      expect(Format.shortenNumber(1234)).toBe('1.2K')
      expect(Format.shortenNumber(12345)).toBe('12.3K')
      expect(Format.shortenNumber(123456)).toBe('123.5K')
    })
  })

  describe('nearestTen', () => {
    it('should pad single digits with leading zero', () => {
      expect(Format.nearestTen(0)).toBe('00')
      expect(Format.nearestTen(5)).toBe('05')
      expect(Format.nearestTen(9)).toBe('09')
    })

    it('should return number as-is for values >= 10', () => {
      expect(Format.nearestTen(10)).toBe(10)
      expect(Format.nearestTen(15)).toBe(15)
      expect(Format.nearestTen(99)).toBe(99)
    })
  })

  describe('camelCase', () => {
    it('should capitalize first letter and lowercase rest', () => {
      expect(Format.camelCase('hello')).toBe('Hello')
      expect(Format.camelCase('HELLO')).toBe('Hello')
      expect(Format.camelCase('hELLO')).toBe('Hello')
    })

    it('should handle single character', () => {
      expect(Format.camelCase('a')).toBe('A')
    })

    it('should handle words with spaces', () => {
      expect(Format.camelCase('hello world')).toBe('Hello world')
    })
  })

  describe('enumeration', () => {
    describe('get', () => {
      it('should convert constant to readable format', () => {
        expect(Format.enumeration.get('MY_CONSTANT')).toBe('My constant')
        expect(Format.enumeration.get('HELLO_WORLD')).toBe('Hello world')
      })

      it('should handle single word', () => {
        expect(Format.enumeration.get('CONSTANT')).toBe('Constant')
      })

      it('should return empty string for null/undefined', () => {
        expect(Format.enumeration.get(null)).toBe('')
        expect(Format.enumeration.get(undefined)).toBe('')
      })
    })

    describe('set', () => {
      it('should convert readable to constant format', () => {
        expect(Format.enumeration.set('My Constant')).toBe('MY_CONSTANT')
        expect(Format.enumeration.set('Hello World')).toBe('HELLO_WORLD')
      })
    })
  })

  describe('fullName', () => {
    it('should format first and last name', () => {
      expect(Format.fullName({ firstName: 'kyle', lastName: 'johnson' })).toBe(
        'Kyle Johnson',
      )
    })

    it('should handle uppercase names', () => {
      expect(Format.fullName({ firstName: 'KYLE', lastName: 'JOHNSON' })).toBe(
        'Kyle Johnson',
      )
    })

    it('should handle only last name', () => {
      expect(Format.fullName({ lastName: 'johnson' })).toBe('Johnson')
    })

    it('should handle only first name', () => {
      expect(Format.fullName({ firstName: 'kyle' })).toBe('Kyle ')
    })

    it('should return empty string for null/undefined', () => {
      expect(Format.fullName(null)).toBe('')
      expect(Format.fullName(undefined)).toBe('')
    })

    it('should handle empty person object', () => {
      expect(Format.fullName({})).toBe('')
    })
  })

  describe('initialAndLastName', () => {
    it('should format as initial and last name', () => {
      expect(
        Format.initialAndLastName({ firstName: 'kyle', lastName: 'johnson' }),
      ).toBe('K. Johnson')
    })

    it('should handle single name', () => {
      expect(Format.initialAndLastName({ lastName: 'johnson' })).toBe('Johnson')
    })

    it('should return empty string for null/undefined', () => {
      expect(Format.initialAndLastName(null)).toBe('')
      expect(Format.initialAndLastName(undefined)).toBe('')
    })
  })

  describe('truncateText', () => {
    it('should truncate text longer than specified length', () => {
      expect(Format.truncateText('hello world', 5)).toBe('hello...')
    })

    it('should not truncate text shorter than specified length', () => {
      expect(Format.truncateText('hello', 10)).toBe('hello')
    })

    it('should return null/undefined as-is', () => {
      expect(Format.truncateText(null, 5)).toBe(null)
      expect(Format.truncateText(undefined, 5)).toBe(undefined)
    })

    it('should handle exact length', () => {
      expect(Format.truncateText('hello', 5)).toBe('hello')
    })
  })

  describe('ordinal', () => {
    it('should add correct suffix for 1st, 2nd, 3rd', () => {
      expect(Format.ordinal(1)).toBe('1st')
      expect(Format.ordinal(2)).toBe('2nd')
      expect(Format.ordinal(3)).toBe('3rd')
    })

    it('should add th suffix for 4-20', () => {
      expect(Format.ordinal(4)).toBe('4th')
      expect(Format.ordinal(11)).toBe('11th')
      expect(Format.ordinal(12)).toBe('12th')
      expect(Format.ordinal(13)).toBe('13th')
    })

    it('should handle 21st, 22nd, 23rd pattern', () => {
      expect(Format.ordinal(21)).toBe('21st')
      expect(Format.ordinal(22)).toBe('22nd')
      expect(Format.ordinal(23)).toBe('23rd')
      expect(Format.ordinal(24)).toBe('24th')
    })

    it('should return empty string for null/undefined/0', () => {
      expect(Format.ordinal(null)).toBe('')
      expect(Format.ordinal(undefined)).toBe('')
      expect(Format.ordinal(0)).toBe('')
    })
  })

  describe('money', () => {
    it('should format currency with pound symbol', () => {
      expect(Format.money(10)).toBe('£10.00')
      expect(Format.money(10.5)).toBe('£10.50')
    })

    it('should add comma separators for thousands', () => {
      expect(Format.money(1000)).toBe('£1,000.00')
      expect(Format.money(1000000)).toBe('£1,000,000.00')
    })

    it('should return FREE for zero', () => {
      expect(Format.money(0)).toBe('FREE')
    })

    it('should return custom default value for zero', () => {
      expect(Format.money(0, 'N/A')).toBe('N/A')
    })

    it('should return FREE for null/undefined values', () => {
      expect(Format.money(null)).toBe('FREE')
      expect(Format.money(undefined)).toBe('FREE')
    })

    it('should return custom default value for null/undefined', () => {
      expect(Format.money(null, 'N/A')).toBe('N/A')
      expect(Format.money(undefined, 'N/A')).toBe('N/A')
    })
  })

  describe('cssImage', () => {
    it('should wrap value in url()', () => {
      expect(Format.cssImage('image.jpg')).toBe('url("image.jpg")')
    })

    it('should return none for null/undefined', () => {
      expect(Format.cssImage(null)).toBe('none')
      expect(Format.cssImage(undefined)).toBe('none')
    })
  })

  describe('trimAndHighlightSpaces', () => {
    it('should replace leading/trailing whitespace groups with single delimiter', () => {
      // The regex replaces entire whitespace groups at start/end with a single delimiter
      expect(Format.trimAndHighlightSpaces('  hello  ')).toBe('␣hello␣')
    })

    it('should replace inline tabs with [TAB]', () => {
      // Tabs in the middle of string are replaced (leading tabs become ␣ first)
      expect(Format.trimAndHighlightSpaces('hello\tworld')).toBe(
        'hello[TAB]world',
      )
    })

    it('should replace newlines with delimiter', () => {
      expect(Format.trimAndHighlightSpaces('hello\nworld')).toBe('hello↵world')
    })

    it('should handle null/undefined', () => {
      expect(Format.trimAndHighlightSpaces(null)).toBe(undefined)
      expect(Format.trimAndHighlightSpaces(undefined)).toBe(undefined)
    })
  })

  describe('userDisplayName', () => {
    it('should return full name if available', () => {
      expect(
        Format.userDisplayName({
          email: 'john@email.com',
          firstName: 'John',
          lastName: 'Doe',
        }),
      ).toBe('John Doe')
    })

    it('should return email if no name available', () => {
      expect(Format.userDisplayName({ email: 'john@email.com' })).toBe(
        'john@email.com',
      )
    })
  })
})
