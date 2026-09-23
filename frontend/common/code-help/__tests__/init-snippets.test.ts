// The templates only need `Constants` for the custom-URL branch. Mocking it
// keeps the legacy Flux stores (which touch `window`) out of this test.
jest.mock('common/constants', () => ({
  __esModule: true,
  default: {
    getFlagsmithSDKUrl: () => 'https://edge.api.flagsmith.com/api/v1/',
    isCustomFlagsmithUrl: () => false,
  },
}))

import initDotnet from 'common/code-help/init/init-dotnet'
import initFlutter from 'common/code-help/init/init-flutter'
import initGo from 'common/code-help/init/init-go'
import initIos from 'common/code-help/init/init-ios'
import initJava from 'common/code-help/init/init-java'
import initJs from 'common/code-help/init/init-js'
import initNextAppRouter from 'common/code-help/init/init-next-app-router'
import initNextPagesRouter from 'common/code-help/init/init-next-pages-router'
import initNode from 'common/code-help/init/init-node'
import initPhp from 'common/code-help/init/init-php'
import initPython from 'common/code-help/init/init-python'
import initReact from 'common/code-help/init/init-react'
import initReactNative from 'common/code-help/init/init-react-native'
import initRuby from 'common/code-help/init/init-ruby'
import initRust from 'common/code-help/init/init-rust'

const ENV_ID = 'test-environment-key'

// Deliberately not a valid identifier in any of the target languages: the
// onboarding lets the user name the flag, and nothing sanitises it.
const FEATURE_NAME = 'show banner-v2'

// Mirrors the subset of `Constants`' keywords the init templates read. Anything
// a template expects but this omits renders as "undefined", which the stray
// interpolation test below catches.
const keywords = {
  FEATURE_NAME,
  // Empty means "one flag only", which is what the onboarding passes.
  FEATURE_NAME_ALT: '',
  LIB_NAME: 'flagsmith',
  LIB_NAME_JAVA: 'FlagsmithClient',
  NPM_CLIENT: '@flagsmith/flagsmith',
  NPM_NODE_CLIENT: '@flagsmith/nodejs',
}

// The Features page keeps two placeholder flags: one for the enabled check, one
// for the value.
const twoFlagKeywords = { ...keywords, FEATURE_NAME_ALT: 'banner_size' }

const snippets: Record<string, string> = {
  '.NET': initDotnet(ENV_ID, keywords),
  'Flutter': initFlutter(ENV_ID, keywords),
  'Go': initGo(ENV_ID, keywords),
  'Java': initJava(ENV_ID, keywords),
  'JavaScript': initJs(ENV_ID, keywords),
  'Next.js (app router)': initNextAppRouter(ENV_ID, keywords),
  'Next.js (pages router)': initNextPagesRouter(ENV_ID, keywords),
  'Node JS': initNode(ENV_ID, keywords),
  'PHP': initPhp(ENV_ID, keywords),
  'Python': initPython(ENV_ID, keywords),
  'React': initReact(ENV_ID, keywords),
  'React Native': initReactNative(ENV_ID, keywords),
  'Ruby': initRuby(ENV_ID, keywords),
  'Rust': initRust(ENV_ID, keywords),
  'iOS': initIos(ENV_ID, keywords),
}

const twoFlagSnippets: Record<string, string> = {
  'JavaScript': initJs(ENV_ID, twoFlagKeywords),
  'Next.js (app router)': initNextAppRouter(ENV_ID, twoFlagKeywords),
  'Node JS': initNode(ENV_ID, twoFlagKeywords),
  'Python': initPython(ENV_ID, twoFlagKeywords),
  'React': initReact(ENV_ID, twoFlagKeywords),
  'Ruby': initRuby(ENV_ID, twoFlagKeywords),
}

const languages = Object.keys(snippets)

describe('code-help init snippets', () => {
  it.each(languages)('%s references only the given flag', (language) => {
    expect(snippets[language]).toContain(FEATURE_NAME)
    expect(snippets[language]).not.toContain('banner_size')
  })

  it.each(languages)('%s interpolates no stray value', (language) => {
    // `${cond && `...`}` renders "false" straight into the snippet when cond is
    // false, e.g. `apiKey = "KEY"false`. A boolean preceded by `: `, `= `, `(`
    // or a comma is a real argument, so only flag the glued-on case.
    expect(snippets[language]).not.toMatch(/[^\s:=(,[]false/)
    // A keyword the template expects but the caller omits renders as undefined.
    expect(snippets[language]).not.toContain('undefined')
  })

  it.each(languages)('%s names no variable after the flag', (language) => {
    // A flag name with a space or hyphen cannot be an identifier.
    expect(snippets[language]).not.toMatch(
      new RegExp(`(const|let|var|final|bool)\\s+${FEATURE_NAME}`),
    )
  })

  it('reads the Python value without json.loads', () => {
    // json.loads needs an import, and throws on a plain string value.
    expect(snippets.Python).not.toContain('json.loads')
  })

  it('defines the flags variable it reads in PHP', () => {
    expect(snippets.PHP).toContain('$flags = $flagsmith->getEnvironmentFlags')
  })

  it('comments Ruby with # rather than //', () => {
    expect(snippets.Ruby).not.toContain('//')
  })

  it('comments .NET with // rather than #', () => {
    expect(snippets['.NET']).not.toContain('#')
  })

  it('passes the Go environment key as a string, not a rune', () => {
    expect(snippets.Go).toContain(`NewClient("${ENV_ID}"`)
  })

  it('renders React Native with View/Text, not web elements', () => {
    // <div>/<p> do not exist in React Native.
    expect(snippets['React Native']).not.toMatch(/<div>|<p>/)
    expect(snippets['React Native']).toContain('<View>')
    expect(snippets['React Native']).toContain('<Text>')
    expect(snippets['React Native']).toContain("from 'react-native'")
  })

  it('gives Go a compilable program', () => {
    // Go rejects unused variables, so reading a flag without printing it does
    // not compile, and a fragment has no package or imports at all.
    expect(snippets.Go).toContain('package main')
    expect(snippets.Go).toContain('func main() {')
    expect(snippets.Go).toContain(
      'flagsmith "github.com/Flagsmith/flagsmith-go-client/v5"',
    )
    expect(snippets.Go).toContain('fmt.Println')
    // v5 takes the context as an argument.
    expect(snippets.Go).toContain('GetEnvironmentFlags(ctx)')
  })

  describe('with a second flag, as the Features page renders it', () => {
    const twoFlagLanguages = Object.keys(twoFlagSnippets)

    it.each(twoFlagLanguages)('%s reads the value off it', (language) => {
      expect(twoFlagSnippets[language]).toContain('banner_size')
    })

    it('subscribes React to both flags', () => {
      expect(twoFlagSnippets.React).toContain(
        `useFlags(['${FEATURE_NAME}', 'banner_size'])`,
      )
      expect(twoFlagSnippets.React).toContain(`flags['banner_size'].value`)
    })

    it.each(['Python', 'Ruby', 'Node JS', 'JavaScript'])(
      '%s labels the printed value with the flag it read',
      (language) => {
        // The value comes off the second flag, so labelling it with the first
        // would tell the reader the wrong flag produced it.
        const printed = twoFlagSnippets[language]
        expect(printed).not.toMatch(/my_cool_feature value/)
        expect(printed).toMatch(/banner_size value/)
      },
    )

    it('still subscribes React to one flag when there is no second', () => {
      expect(snippets.React).toContain(`useFlags(['${FEATURE_NAME}'])`)
      expect(snippets.React).toContain(`flags['${FEATURE_NAME}'].value`)
    })
  })
})
