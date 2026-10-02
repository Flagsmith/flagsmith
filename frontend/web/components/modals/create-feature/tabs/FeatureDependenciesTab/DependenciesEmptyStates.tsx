import { FC } from 'react'
import EmptyState from 'components/EmptyState'

const DOCS_URL = 'https://docs.flagsmith.com/basic-features/managing-features'

type PrerequisitesEmptyStateProps = {
  featureName: string
  // Dependencies are one layer deep, so a feature other features already
  // depend on cannot take prerequisites of its own.
  isPrerequisite: boolean
}

// The Add prerequisite button sits directly below this panel, so neither state
// repeats it.
export const PrerequisitesEmptyState: FC<PrerequisitesEmptyStateProps> = ({
  featureName,
  isPrerequisite,
}) =>
  isPrerequisite ? (
    <EmptyState
      className='p-4'
      icon='layers'
      title='Other features depend on this flag'
      description={
        <>
          Dependencies are one layer deep, so <strong>{featureName}</strong>{' '}
          cannot have prerequisites of its own. Remove it as a prerequisite of
          the features below to add some here.
        </>
      }
      docsUrl={DOCS_URL}
    />
  ) : (
    <EmptyState
      className='p-4'
      icon='layers'
      title='No prerequisites'
      description={
        <>
          <strong>{featureName}</strong> is evaluated independently of every
          other feature. Add a prerequisite to gate it behind another flag.
        </>
      }
    />
  )

type DependentsEmptyStateProps = {
  featureName: string
  hasPrerequisites: boolean
}

export const DependentsEmptyState: FC<DependentsEmptyStateProps> = ({
  featureName,
  hasPrerequisites,
}) =>
  hasPrerequisites ? (
    <EmptyState
      className='p-4'
      icon='layers'
      title='No dependent features'
      description={
        <>
          <strong>{featureName}</strong> has prerequisites of its own.
          Dependencies are only one layer deep, so other features cannot depend
          on it.
        </>
      }
    />
  ) : (
    // Nothing is stopping this one from gaining dependents, so it says where
    // they come from rather than only that there are none.
    <EmptyState
      className='p-4'
      icon='layers'
      title='No dependent features'
      description={
        <>
          Add <strong>{featureName}</strong> as a prerequisite of another flag
          and that flag will appear here.
        </>
      }
    />
  )
