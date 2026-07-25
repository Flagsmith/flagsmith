// Snippets for every SDK we support, sourced from the maintained
// `Constants.codeHelp` (the same install/init the rest of the app uses, so
// they don't drift). Two adaptations for this page:
//   1. codeHelp snippets are authored for innerHTML rendering, so they carry
//      HTML entities (&lt; etc.). We render via <Highlight> (escaping on), so
//      we unescape first.
//   2. They use a placeholder flag name; we swap it for the user's real flag,
//      so the snippet references the flag this onboarding actually created.
// The SDK list itself (labels, logos, codeHelp keys) lives in ./sdkLangs.
import Constants from 'common/constants'
import { SdkLang } from './sdkLangs'

// Mirrors Constants' `keywords.FEATURE_NAME`. Kept local (keywords isn't
// exported); if that placeholder ever changes, update this too.
const PLACEHOLDER_FLAG = 'my_cool_feature'

const unescapeHtml = (s: string): string =>
  s
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&#39;/g, "'")
    .replace(/&quot;/g, '"')
    .replace(/&amp;/g, '&')

export type SdkSnippet = {
  install: string
  // Present for npm-based SDKs (codeHelp ships both managers in one block);
  // drives the npm/yarn pills so each shows a single copy-pasteable line.
  installYarn?: string
  wire: string
  language: string
}

// codeHelp's npm-based install is a "// npm\n<cmd>\n\n// yarn\n<cmd>" block.
// Split it into the two single commands so the user copies one clean line, not
// the whole annotated block. Non-npm installs (pip, gem, go get…) pass through.
const parseInstall = (
  raw: string,
): { install: string; installYarn?: string } => {
  const npm = raw.match(/\/\/\s*npm\s*\n(.+)/)
  const yarn = raw.match(/\/\/\s*yarn\s*\n(.+)/)
  if (npm && yarn) {
    return { install: npm[1].trim(), installYarn: yarn[1].trim() }
  }
  return { install: raw.trim() }
}

export const getSdkSnippet = (
  lang: SdkLang,
  environmentKey: string,
  featureName: string,
): SdkSnippet => {
  const installs = Constants.codeHelp.INSTALL as Record<string, string>
  const inits = Constants.codeHelp.INIT(environmentKey) as Record<
    string,
    string
  >
  const wire = unescapeHtml(inits[lang.initKey ?? lang.codeHelpKey] ?? '')
    .split(PLACEHOLDER_FLAG)
    .join(featureName)
  return {
    language: lang.language,
    ...parseInstall(unescapeHtml(installs[lang.codeHelpKey] ?? '')),
    wire: wire.trim(),
  }
}
