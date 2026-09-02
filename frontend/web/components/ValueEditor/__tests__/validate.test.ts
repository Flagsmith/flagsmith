import { validateValue } from 'components/ValueEditor/validate'

describe('validateValue', () => {
  describe('txt', () => {
    it('never reports an error, whatever the value', () => {
      expect(validateValue('txt', 'anything at all')).toBe(false)
      expect(validateValue('txt', '{ not json')).toBe(false)
      expect(validateValue('txt', '')).toBe(false)
    })
  })

  describe('json', () => {
    it('accepts objects, arrays and scalars', () => {
      expect(validateValue('json', '{ "a": 1 }')).toBe(false)
      expect(validateValue('json', '[1, 2, 3]')).toBe(false)
      expect(validateValue('json', '"a string"')).toBe(false)
      expect(validateValue('json', '12')).toBe(false)
    })

    it('reports the parser message for malformed input', () => {
      expect(validateValue('json', '{ "a": ')).toEqual(expect.any(String))
      expect(validateValue('json', '{ "a": 1,, }')).toEqual(expect.any(String))
    })

    it('reports an error for an empty value', () => {
      expect(validateValue('json', '')).toEqual(expect.any(String))
    })
  })

  describe('yaml', () => {
    it('accepts a mapping', () => {
      expect(validateValue('yaml', 'colour: blue\nsize: 12')).toBe(false)
    })

    it('accepts an empty value', () => {
      expect(validateValue('yaml', '')).toBe(false)
    })

    it('reports the parser message for malformed input', () => {
      expect(validateValue('yaml', 'a: "unclosed')).toEqual(expect.any(String))
      expect(validateValue('yaml', 'a:\n  b: 1\n c: 2')).toEqual(
        expect.any(String),
      )
    })
  })

  describe('ini (toml)', () => {
    it('accepts a table', () => {
      expect(validateValue('ini', '[owner]\nname = "Tom"')).toBe(false)
    })

    it('reports the parser message for malformed input', () => {
      expect(validateValue('ini', 'name = ')).toEqual(expect.any(String))
    })
  })

  // The xml branch needs DOMParser, which jest's node environment does not
  // provide. Covering it means jest-environment-jsdom, which is a wider
  // decision than this file.
  describe('xml', () => {
    it.todo('accepts a well-formed document (needs jsdom)')
    it.todo('reports an error for mismatched tags (needs jsdom)')
  })
})
