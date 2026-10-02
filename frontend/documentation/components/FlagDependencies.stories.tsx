import type { Meta, StoryObj } from 'storybook'

import { DependencyEdge } from 'common/types/responses'
import {
  BlockedBanner,
  DependentFeatures,
  DependentsEmptyState,
  FeatureDependenciesSkeleton,
  PrerequisitesEmptyState,
  PrerequisitesTable,
  toPrerequisiteRow,
} from 'components/modals/create-feature/tabs/FeatureDependenciesTab'

const FEATURE = 'checkout_v2'
const ENVIRONMENT = 'Development'

const edge = (
  name: string,
  id: number,
  { isSystem = true } = {},
): DependencyEdge =>
  ({
    feature: { id: 1, name: FEATURE },
    prerequisite: { id, name },
    segment: {
      condition_json_path: '$[0].conditions[0]',
      id: 900 + id,
      is_system: isSystem,
      name: `${FEATURE}-depends-on-${name}`,
      rules: [],
    },
  } as unknown as DependencyEdge)

const billing = toPrerequisiteRow(edge('billing_engine_v2', 101), true)
const payments = toPrerequisiteRow(edge('payment_provider', 102), false)
// A segment written by hand: neither its operator nor its override value is in
// the response, so the row abstains.
const handWritten = toPrerequisiteRow(
  edge('legacy_kill_switch', 103, { isSystem: false }),
  false,
)

const noop = () => undefined

// Every story renders inside the tab's own width, so the table and the banner
// wrap the way they do in the modal.
const Tab = ({ children }: { children: React.ReactNode }) => (
  <div className='feature-dependencies' style={{ maxWidth: 720 }}>
    {children}
  </div>
)

const Panel = ({ children }: { children: React.ReactNode }) => (
  <Tab>
    <div className='feature-dependencies__panel'>{children}</div>
  </Tab>
)

const meta: Meta = {
  parameters: {
    docs: {
      description: {
        component:
          'The pieces the Dependencies tab is built from. Status is the prerequisite’s own state; Satisfies is whether that state meets this flag’s rule.',
      },
    },
  },
  title: 'Components/Flag dependencies',
}
export default meta

type Story = StoryObj

export const PrerequisitesSatisfied: Story = {
  render: () => (
    <Panel>
      <PrerequisitesTable rows={[billing]} canManage onRemove={noop} />
    </Panel>
  ),
}

export const PrerequisitesMixed: Story = {
  render: () => (
    <Panel>
      <PrerequisitesTable
        rows={[billing, payments, handWritten]}
        canManage
        onRemove={noop}
      />
    </Panel>
  ),
}

export const PrerequisitesReadOnly: Story = {
  name: 'Prerequisites without permission',
  render: () => (
    <Panel>
      <PrerequisitesTable
        rows={[billing, payments]}
        canManage={false}
        onRemove={noop}
      />
    </Panel>
  ),
}

export const PrerequisiteRemoving: Story = {
  name: 'Prerequisite being removed',
  render: () => (
    <Panel>
      <PrerequisitesTable
        rows={[billing, payments]}
        canManage
        isRemoving={payments.edge.prerequisite.id}
        onRemove={noop}
      />
    </Panel>
  ),
}

export const BannerBlocked: Story = {
  name: 'Banner, one prerequisite off',
  render: () => (
    <Tab>
      <BlockedBanner environmentName={ENVIRONMENT} rows={[billing, payments]} />
    </Tab>
  ),
}

export const BannerAllOff: Story = {
  name: 'Banner, every prerequisite off',
  render: () => (
    <Tab>
      <BlockedBanner environmentName={ENVIRONMENT} rows={[payments]} />
    </Tab>
  ),
}

export const NoPrerequisites: Story = {
  render: () => (
    <Panel>
      <PrerequisitesEmptyState featureName={FEATURE} isPrerequisite={false} />
    </Panel>
  ),
}

export const CannotTakePrerequisites: Story = {
  name: 'Prerequisites unavailable',
  render: () => (
    <Panel>
      <PrerequisitesEmptyState featureName={FEATURE} isPrerequisite />
    </Panel>
  ),
}

export const Dependents: Story = {
  render: () => (
    <Tab>
      <DependentFeatures
        featureName={FEATURE}
        edges={[edge('express_lane', 201), edge('one_click_pay', 202)]}
        hasPrerequisites={false}
        onSelect={noop}
      />
    </Tab>
  ),
}

export const NoDependents: Story = {
  render: () => (
    <Panel>
      <DependentsEmptyState featureName={FEATURE} hasPrerequisites={false} />
    </Panel>
  ),
}

export const NoDependentsBecausePrerequisites: Story = {
  name: 'No dependents, flag has prerequisites',
  render: () => (
    <Panel>
      <DependentsEmptyState featureName={FEATURE} hasPrerequisites />
    </Panel>
  ),
}

export const Loading: Story = {
  render: () => (
    <Tab>
      <FeatureDependenciesSkeleton />
    </Tab>
  ),
}
