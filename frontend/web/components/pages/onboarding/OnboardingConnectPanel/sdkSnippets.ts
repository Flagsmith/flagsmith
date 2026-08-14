// Snippets for every SDK we support, sourced from the maintained
// `Constants.codeHelp` (the same install/init the rest of the app uses, so
// they don't drift). We pass the flag this onboarding created, which builds the
// snippets around that one flag rather than codeHelp's two placeholders.
// The SDK list itself (labels, logos, codeHelp keys) lives in ./sdkLangs.
import Constants from 'common/constants'
import { SdkLang } from './sdkLangs'

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
  const inits = Constants.codeHelp.INIT(environmentKey, featureName) as Record<
    string,
    string
  >
  return {
    language: lang.language,
    ...parseInstall(installs[lang.codeHelpKey] ?? ''),
    wire: (inits[lang.initKey ?? lang.codeHelpKey] ?? '').trim(),
  }
}
