// import propTypes from 'prop-types';
import React from 'react'
import TabItem from 'components/navigation/TabMenu/TabItem'
import Tabs from 'components/navigation/TabMenu/Tabs'
import CompareEnvironments from 'components/CompareEnvironments'
import CompareFeatures from 'components/CompareFeatures'
import ConfigProvider from 'common/providers/ConfigProvider'
import CompareIdentities from 'components/CompareIdentities'
import PageTitle from 'components/PageTitle'
import { useRouteMatch } from 'react-router-dom'
import { useRouteContext } from 'components/providers/RouteContext'
import { useTabUrlSync } from 'common/hooks/useTabUrlSync'

const COMPARE_TABS = ['Environments', 'Feature Values', 'Identities']

const ComparePage = () => {
  const { projectId } = useRouteContext()
  const match = useRouteMatch()
  const [tab, setTab] = useTabUrlSync('tab', COMPARE_TABS)

  return (
    <div className='app-container container'>
      <PageTitle className='mb-2' title={'Compare'}>
        Compare data across your environments, features and identities.
      </PageTitle>
      <Tabs className='mt-0' value={tab} onChange={setTab}>
        <TabItem tabLabel='Environments'>
          <div className='mt-4'>
            <CompareEnvironments
              projectId={projectId}
              environmentId={match.params.environmentId}
            />
          </div>
        </TabItem>
        <TabItem tabLabel='Feature Values'>
          <div className='mt-4'>
            <CompareFeatures projectId={projectId} />
          </div>
        </TabItem>
        <TabItem tabLabel='Identities'>
          <div className='mt-4'>
            <CompareIdentities
              environmentId={match.params.environmentId}
              projectId={projectId}
            />
          </div>
        </TabItem>
      </Tabs>
    </div>
  )
}

ComparePage.displayName = 'ComparePage'

export default ConfigProvider(ComparePage)
