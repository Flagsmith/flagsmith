import React, { FC, useCallback } from 'react'
import { RouterChildContext } from 'react-router'
import PageTitle from 'components/PageTitle'
import FeatureSelect from 'components/FeatureSelect'
import Utils from 'common/utils/utils'
import ConfigProvider from 'common/providers/ConfigProvider'
import FeatureAnalytics from 'components/FeatureAnalytics'
import InputGroup from 'components/base/forms/InputGroup'
import { useGetEnvironmentsQuery } from 'common/services/useEnvironment'

type FeatureAnalyticsPageType = {
  router: RouterChildContext['router']
  match: {
    params: {
      environmentId: string
      projectId: string
    }
  }
}

const FeatureAnalyticsPage: FC<FeatureAnalyticsPageType> = ({
  match,
  router,
}) => {
  const { data: environments } = useGetEnvironmentsQuery({
    projectId: match.params.projectId,
  })
  const params = Utils.fromParam()
  const selectedFlag = params.feature
  const setSelectedFlag = useCallback(
    (flag) => {
      router.history.replace(`${document.location.pathname}?feature=${flag}`)
    },
    [router],
  )
  return (
    <div className='app-container container'>
      <PageTitle title={'Feature Analytics'}>
        <div>View how often your applications are evaluating features.</div>
      </PageTitle>
      <div className='row'>
        <div className='col-md-4'>
          <InputGroup
            title='Feature'
            component={
              <FeatureSelect
                autoSelectFirst
                projectId={match.params.projectId}
                onChange={setSelectedFlag}
                value={selectedFlag}
              />
            }
          />
        </div>
      </div>
      {!!selectedFlag && environments && (
        <FeatureAnalytics
          projectId={match.params.projectId}
          featureId={selectedFlag}
          defaultEnvironmentIds={environments.results.map((v) => `${v.id}`)}
        />
      )}
    </div>
  )
}

export default ConfigProvider(FeatureAnalyticsPage)
