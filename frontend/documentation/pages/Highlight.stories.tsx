import type { Meta, StoryObj } from 'storybook'

import Highlight from 'components/Highlight'

const meta: Meta<typeof Highlight> = {
  component: Highlight,
  parameters: {
    docs: {
      description: {
        component:
          'The code wrapper: renders a `<pre><code class="hljs">` block and runs ' +
          'highlight.js over it. This is what the shared code theme styles (surface, ' +
          'border, syntax palette). Toggle the theme in the toolbar to QA light vs dark; ' +
          '`className` is the highlight.js language.',
      },
    },
    layout: 'padded',
  },
  title: 'Components/Highlight',
}

export default meta

type Story = StoryObj<typeof Highlight>

const js = `// Initialise the client
import flagsmith from 'flagsmith'

flagsmith.init({
  environmentID: 'YOUR_ENVIRONMENT_KEY',
  onChange: () => {
    const bannerSize = flagsmith.getValue('banner_size')
  },
})`

const ts = `import { useFlags } from 'flagsmith/react'

type FlagName = 'banner_size' | 'my_feature'

const flags = useFlags<FlagName>(['banner_size'])
const size: number = flags.banner_size.value ?? 0`

const json = `{
  "flags": [
    { "feature": "banner_size", "enabled": true, "value": 42 },
    { "feature": "my_feature", "enabled": false, "value": null }
  ]
}`

const yaml = `flags:
  - feature: banner_size
    enabled: true
    value: 42`

// Mirrors the React SDK snippet in code-help: markup tags inside JavaScript.
const jsx = `export function HomePage() {
  const flags = useFlags(['banner_size'])
  return (
    <Row className="banner">
      <Flag name="banner_size" size={flags.banner_size.value} />
    </Row>
  )
}`

export const JavaScript: Story = {
  args: { children: js, className: 'javascript', forceExpanded: true },
}

export const TypeScript: Story = {
  args: { children: ts, className: 'typescript', forceExpanded: true },
}

export const Json: Story = {
  args: { children: json, className: 'json', forceExpanded: true },
}

export const Yaml: Story = {
  args: { children: yaml, className: 'yaml', forceExpanded: true },
}

export const Jsx: Story = {
  args: { children: jsx, className: 'javascript', forceExpanded: true },
}

// Embedded variant: transparent, for code whose container owns the surface.
export const Embedded: Story = {
  args: {
    children: js,
    className: 'javascript',
    embedded: true,
    forceExpanded: true,
  },
}
