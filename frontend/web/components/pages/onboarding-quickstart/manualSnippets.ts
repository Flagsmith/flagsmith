// Per-language "Connect your code" snippets for the single-page onboarding,
// matching the design: install the SDK, then initialise it and gate the demo
// feature on the user's real flag. Deliberately simple (no onChange/value
// scaffolding) — the goal is the first evaluation, not a tour of the API.
//
// The API URL is injected only when the app isn't on the default SaaS endpoint
// (staging / self-hosted), using each SDK's own option name. On SaaS nothing is
// injected, so the snippet matches the design exactly.

export type ManualLang =
  | 'React'
  | 'JavaScript'
  | 'Python'
  | 'Node.js'
  | 'Go'
  | 'Ruby'

export const MANUAL_LANGS: ManualLang[] = [
  'React',
  'JavaScript',
  'Python',
  'Node.js',
  'Go',
  'Ruby',
]

export type ManualSnippet = {
  // highlight.js class for the wire snippet (install is always shell/bash)
  hljs: string
  install: string
  // yarn equivalent for npm-based SDKs; when present the install block shows
  // npm/yarn pills. Omitted for non-npm package managers (pip, go get, gem…).
  installYarn?: string
  wire: string
}

type Args = {
  apiUrl: string
  environmentKey: string
  featureName: string
  isCustomUrl: boolean
}

export const getManualSnippets = ({
  apiUrl,
  environmentKey,
  featureName,
  isCustomUrl,
}: Args): Record<ManualLang, ManualSnippet> => {
  const jsApi = isCustomUrl ? `\n  api: '${apiUrl}',` : ''
  const pyApi = isCustomUrl ? `,\n    api_url="${apiUrl}"` : ''
  const nodeApi = isCustomUrl ? `, apiUrl: '${apiUrl}'` : ''
  const rubyApi = isCustomUrl ? `, api_url: '${apiUrl}'` : ''
  const goApi = isCustomUrl ? `, flagsmith.WithBaseURL("${apiUrl}")` : ''

  // React and JavaScript share the vanilla client snippet, mirroring the design.
  const jsWire = `import flagsmith from 'flagsmith'

flagsmith.init({
  environmentID: '${environmentKey}',${jsApi}
})

if (flagsmith.hasFeature('${featureName}')) {
  renderNewFeature()
}`

  return {
    'Go': {
      hljs: 'go',
      install: 'go get github.com/Flagsmith/flagsmith-go-client/v3',
      wire: `client := flagsmith.NewClient("${environmentKey}"${goApi})
flags, _ := client.GetEnvironmentFlags(ctx)

if enabled, _ := flags.IsFeatureEnabled("${featureName}"); enabled {
    renderNewFeature()
}`,
    },
    'JavaScript': {
      hljs: 'javascript',
      install: 'npm install flagsmith --save',
      installYarn: 'yarn add flagsmith',
      wire: jsWire,
    },
    'Node.js': {
      hljs: 'javascript',
      install: 'npm install flagsmith-nodejs --save',
      installYarn: 'yarn add flagsmith-nodejs',
      wire: `import Flagsmith from 'flagsmith-nodejs'

const flagsmith = new Flagsmith({ environmentKey: '${environmentKey}'${nodeApi} })
const flags = await flagsmith.getEnvironmentFlags()

if (flags.isFeatureEnabled('${featureName}')) {
  renderNewFeature()
}`,
    },
    'Python': {
      hljs: 'python',
      install: 'pip install flagsmith',
      wire: `from flagsmith import Flagsmith

flagsmith = Flagsmith(
    environment_key="${environmentKey}"${pyApi}
)
flags = flagsmith.get_environment_flags()

if flags.is_feature_enabled("${featureName}"):
    render_new_feature()`,
    },
    'React': {
      hljs: 'javascript',
      install: 'npm install flagsmith --save',
      installYarn: 'yarn add flagsmith',
      wire: jsWire,
    },
    'Ruby': {
      hljs: 'ruby',
      install: 'gem install flagsmith',
      wire: `flagsmith = Flagsmith::Client.new(environment_key: '${environmentKey}'${rubyApi})
flags = flagsmith.get_environment_flags

if flags.is_feature_enabled('${featureName}')
  render_new_feature
end`,
    },
  }
}
