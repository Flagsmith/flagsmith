import { useState } from 'react'
import type { Meta, StoryObj } from 'storybook'

import { DependencyEdge } from 'common/types/responses'
import FeatureDependenciesSkeleton from 'components/modals/create-feature/tabs/FeatureDependenciesTab/FeatureDependenciesSkeleton'
import FeatureDependenciesView from 'components/modals/create-feature/tabs/FeatureDependenciesTab/FeatureDependenciesView'
import { PrerequisiteRow } from 'components/modals/create-feature/tabs/FeatureDependenciesTab/PrerequisitesTable'
import 'components/modals/create-feature/tabs/FeatureDependenciesTab/FeatureDependenciesTab.scss'

const ENVIRONMENT = 'Development'

// Flags to pick from. `enabled` drives whether a prerequisite reads as met, the
// same as the feature's real state does in the app.
const CATALOGUE = [
  { enabled: true, id: 101, name: 'billing_engine_v2' },
  { enabled: false, id: 102, name: 'payment_provider' },
  { enabled: true, id: 103, name: 'dark_mode' },
  { enabled: false, id: 104, name: 'beta_programme' },
  { enabled: true, id: 105, name: 'search_ranking' },
]

const edge = (
  feature: { id: number; name: string },
  prerequisite: { id: number; name: string },
  isSystem = true,
): DependencyEdge => ({
  feature,
  prerequisite,
  segment: {
    condition_json_path: '$[0].conditions[0]',
    id: 900 + prerequisite.id,
    is_system: isSystem,
    name: `${feature.name}-dependencies`,
    rules: [
      {
        conditions: [
          {
            operator: 'NOT_EQUAL',
            property: `$.flags["${prerequisite.name}"].enabled`,
            value: 'true',
          },
        ],
        rules: [],
        type: 'ANY',
        version_of: undefined,
      },
    ],
  },
})

type PrototypeProps = {
  featureName: string
  initialPrerequisites?: { id: number; name: string; isSystem?: boolean }[]
  dependents?: { id: number; name: string }[]
  canManage?: boolean
}

// Holds the same state the tab holds, so adding and removing behave as they do
// against a real API, minus the request.
const Prototype = ({
  canManage = true,
  dependents = [],
  featureName,
  initialPrerequisites = [],
}: PrototypeProps) => {
  const self = { id: 1, name: featureName }
  const [prerequisites, setPrerequisites] = useState(initialPrerequisites)
  const [conflict, setConflict] = useState<string | null>(null)
  const [highlightedId, setHighlightedId] = useState<number | undefined>()

  const rows: PrerequisiteRow[] = prerequisites.map((prerequisite) => ({
    edge: edge(self, prerequisite, prerequisite.isSystem ?? true),
    isEnabled: !!CATALOGUE.find((flag) => flag.id === prerequisite.id)?.enabled,
    isMet: !!CATALOGUE.find((flag) => flag.id === prerequisite.id)?.enabled,
  }))

  const taken = prerequisites.map((prerequisite) => prerequisite.id)
  const available = CATALOGUE.filter((flag) => !taken.includes(flag.id))

  return (
    <div className='p-4' style={{ margin: '0 auto', maxWidth: 820 }}>
      <FeatureDependenciesView
        featureName={featureName}
        environmentName={ENVIRONMENT}
        rows={rows}
        dependentEdges={dependents.map((dependent) => edge(dependent, self))}
        canManage={canManage}
        conflict={conflict}
        highlightedId={highlightedId}
        onRemove={(removed) => {
          setConflict(null)
          setPrerequisites((current) =>
            current.filter((p) => p.id !== removed.prerequisite.id),
          )
        }}
        onSelectFeature={() =>
          setConflict(
            'Opening another feature is not wired up in this prototype.',
          )
        }
        addControl={
          // The same Select the app uses; Storybook registers it as a global
          // to match project-components.js.
          <Select
            data-test='add-prerequisite'
            isDisabled={!available.length}
            placeholder={
              available.length
                ? 'Add a prerequisite flag...'
                : 'Every flag is already a prerequisite'
            }
            value={null}
            options={available.map((flag) => ({
              label: flag.name,
              value: flag.id,
            }))}
            onChange={(option: { value: number } | null) => {
              const flag = CATALOGUE.find((f) => f.id === option?.value)
              if (!flag) return
              setConflict(null)
              setPrerequisites((current) => [...current, flag])
              setHighlightedId(flag.id)
              setTimeout(() => setHighlightedId(undefined), 2000)
            }}
          />
        }
      />
    </div>
  )
}

const meta: Meta<typeof Prototype> = {
  component: Prototype,
  parameters: {
    docs: {
      description: {
        component:
          'The Dependencies tab in its modal, with working state. Adding and removing prerequisites update the list, the warning count and the empty states, so the whole flow can be walked without a running API. Whether a prerequisite reads as met comes from a fixed catalogue: billing_engine_v2, dark_mode and search_ranking are on, the rest are off.',
      },
    },
    layout: 'fullscreen',
  },
  title: 'Pages/Flag Dependencies',
}
export default meta

type Story = StoryObj<typeof Prototype>

export const CleanSlate: Story = {
  args: { featureName: 'dark_mode' },
}

export const HasPrerequisites: Story = {
  args: {
    featureName: 'marketplace',
    initialPrerequisites: [
      { id: 101, name: 'billing_engine_v2' },
      { id: 102, name: 'payment_provider' },
    ],
  },
}

export const IsAPrerequisite: Story = {
  args: {
    dependents: [
      { id: 7, name: 'checkout_express_lane' },
      { id: 8, name: 'one_click_pay' },
    ],
    featureName: 'billing_engine_v2',
  },
}

export const FromASegment: Story = {
  args: {
    featureName: 'marketplace',
    initialPrerequisites: [
      { id: 101, name: 'billing_engine_v2' },
      // Hand-written in a segment, so it has no remove control.
      { id: 105, isSystem: false, name: 'search_ranking' },
    ],
  },
}

export const WithoutPermission: Story = {
  args: {
    canManage: false,
    featureName: 'marketplace',
    initialPrerequisites: [
      { id: 101, name: 'billing_engine_v2' },
      { id: 102, name: 'payment_provider' },
    ],
  },
}

export const Loading: Story = {
  render: () => (
    <div className='p-4' style={{ margin: '0 auto', maxWidth: 820 }}>
      <FeatureDependenciesSkeleton />
    </div>
  ),
}
