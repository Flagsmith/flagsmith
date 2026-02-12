import React, { FC } from 'react'
import { useRouteContext } from 'components/providers/RouteContext'
import { useGetTagsQuery } from 'common/services/useTag'
import FeaturesPage from './features/FeaturesPage'

const ExperimentsPage: FC = () => {
  const routeContext = useRouteContext()
  const projectId = routeContext.projectId!

  const { data: tags, isLoading } = useGetTagsQuery({ projectId })

  if (isLoading) {
    return (
      <div className='text-center'>
        <Loader />
      </div>
    )
  }

  const experimentTag = tags?.find(
    (t) => t.label.toLowerCase() === 'experiment',
  )

  if (!experimentTag) {
    return (
      <div data-test='experiments-page' className='app-container container'>
        <h3>Experiments</h3>
        <p>You don't have any experiment running at the moment</p>
      </div>
    )
  }

  return (
    <FeaturesPage
      pageTitle='Experiments'
      forcedTagIds={[experimentTag.id]}
      defaultExperiment
    />
  )
}

export default ExperimentsPage
