import React, { FC, useState } from 'react'
import Button from 'components/base/forms/Button'
import Icon from 'components/icons/Icon'
import Tabs from 'components/navigation/TabMenu/Tabs'
import TabItem from 'components/navigation/TabMenu/TabItem'
import Utils from 'common/utils/utils'

// Purpose-specific snippet for the onboarding "make a first flag eval" moment.
// Deliberately minimal — 3–5 lines per language, no onChange callbacks,
// no value comparisons. The user's actual feature name is interpolated so
// the code they paste references their flag, not a placeholder.
//
// Distinct from `components/CodeHelp` which is for reference/learning in the
// rest of the app and shows richer SDK patterns.

type Language = {
  id: string
  label: string
}

const LANGUAGES: Language[] = [
  { id: 'js', label: 'JavaScript' },
  { id: 'react', label: 'React' },
  { id: 'node', label: 'Node.js' },
  { id: 'python', label: 'Python' },
  { id: 'go', label: 'Go' },
  { id: 'java', label: 'Java' },
  { id: 'ruby', label: 'Ruby' },
  { id: 'php', label: 'PHP' },
  { id: 'dotnet', label: '.NET' },
  { id: 'rust', label: 'Rust' },
  { id: 'flutter', label: 'Flutter' },
  { id: 'ios', label: 'iOS' },
  { id: 'curl', label: 'cURL' },
]

const buildSnippet = (
  languageId: string,
  environmentKey: string,
  featureName: string,
): string => {
  switch (languageId) {
    case 'react':
      return `import { FlagsmithProvider } from 'flagsmith/react'
import flagsmith from '@flagsmith/flagsmith'

<FlagsmithProvider options={{ environmentID: '${environmentKey}' }} flagsmith={flagsmith}>
  <App />
</FlagsmithProvider>`
    case 'node':
      return `import Flagsmith from 'flagsmith-nodejs'

const flagsmith = new Flagsmith({ environmentKey: '${environmentKey}' })
const flags = await flagsmith.getEnvironmentFlags()
console.log('${featureName}:', flags.isFeatureEnabled('${featureName}'))`
    case 'python':
      return `from flagsmith import Flagsmith

flagsmith = Flagsmith(environment_key="${environmentKey}")
flags = flagsmith.get_environment_flags()
print("${featureName}:", flags.is_feature_enabled("${featureName}"))`
    case 'go':
      return `client := flagsmith.NewClient("${environmentKey}")
flags, _ := client.GetEnvironmentFlags()
enabled, _ := flags.IsFeatureEnabled("${featureName}")
fmt.Printf("${featureName}: %v\\n", enabled)`
    case 'java':
      return `FlagsmithClient client = FlagsmithClient.newBuilder()
    .setApiKey("${environmentKey}")
    .build();
Flags flags = client.getEnvironmentFlags();
System.out.println("${featureName}: " + flags.isFeatureEnabled("${featureName}"));`
    case 'ruby':
      return `flagsmith = Flagsmith::Client.new(environment_key: '${environmentKey}')
flags = flagsmith.get_environment_flags
puts "${featureName}: #{flags.is_feature_enabled('${featureName}')}"`
    case 'php':
      return `$flagsmith = new \\Flagsmith\\Flagsmith('${environmentKey}');
$flags = $flagsmith->getEnvironmentFlags();
echo "${featureName}: " . ($flags->isFeatureEnabled('${featureName}') ? 'true' : 'false');`
    case 'dotnet':
      return `var flagsmith = new FlagsmithClient(new FlagsmithConfiguration {
    EnvironmentKey = "${environmentKey}"
});
var flags = await flagsmith.GetEnvironmentFlags();
Console.WriteLine($"${featureName}: {await flags.IsFeatureEnabled(\\"${featureName}\\")}");`
    case 'rust':
      return `let flagsmith = Flagsmith::new("${environmentKey}".to_string(), None);
let flags = flagsmith.get_environment_flags().await?;
println!("${featureName}: {}", flags.is_feature_enabled("${featureName}")?);`
    case 'flutter':
      return `await Flagsmith.init(apiKey: '${environmentKey}');
final flags = await Flagsmith.getEnvironmentFlags();
print('${featureName}: \${flags.isFeatureEnabled('${featureName}')}');`
    case 'ios':
      return `Flagsmith.shared.apiKey = "${environmentKey}"
Flagsmith.shared.getFeatureFlags { _ in
    let enabled = Flagsmith.shared.hasFeatureFlag(withID: "${featureName}")
    print("${featureName}: \\(enabled)")
}`
    case 'curl':
      return `curl -H 'X-Environment-Key: ${environmentKey}' \\
  https://edge.api.flagsmith.com/api/v1/flags/`
    case 'js':
    default:
      return `import flagsmith from '@flagsmith/flagsmith'

await flagsmith.init({ environmentID: '${environmentKey}' })
console.log('${featureName}:', flagsmith.hasFeature('${featureName}'))`
  }
}

type CodeSnippetProps = {
  environmentKey: string
  featureName: string
  onCopy?: (languageId: string) => void
}

const CodeSnippet: FC<CodeSnippetProps> = ({
  environmentKey,
  featureName,
  onCopy,
}) => {
  const [copiedLang, setCopiedLang] = useState<string | null>(null)

  const handleCopy = (languageId: string, snippet: string) => {
    Utils.copyToClipboard(snippet)
    setCopiedLang(languageId)
    onCopy?.(languageId)
    setTimeout(() => setCopiedLang(null), 1500)
  }

  return (
    <div className='onboarding-quickstart__snippet rounded-lg border border-default bg-surface-default'>
      <Tabs uncontrolled hideNavOnSingleTab={false}>
        {LANGUAGES.map((language) => {
          const snippet = buildSnippet(language.id, environmentKey, featureName)
          const isCopied = copiedLang === language.id
          return (
            <TabItem key={language.id} tabLabel={language.label}>
              <div className='onboarding-quickstart__snippet-body p-3'>
                <div className='d-flex align-items-center justify-content-between mb-2'>
                  <span className='text-muted'>
                    Paste into your app and run it.
                  </span>
                  <Button
                    theme='outline'
                    size='small'
                    onClick={() => handleCopy(language.id, snippet)}
                  >
                    <span className='d-inline-flex align-items-center gap-1'>
                      <Icon name='copy' width={14} />
                      {isCopied ? 'Copied' : 'Copy'}
                    </span>
                  </Button>
                </div>
                <pre className='onboarding-quickstart__code-block m-0 p-3 rounded-md'>
                  <code>{snippet}</code>
                </pre>
              </div>
            </TabItem>
          )
        })}
      </Tabs>
    </div>
  )
}

export default CodeSnippet
