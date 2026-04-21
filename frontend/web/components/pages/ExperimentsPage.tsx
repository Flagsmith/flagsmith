import React, { FC } from 'react'
import ExperimentsListPage from 'components/experiments-v2/ExperimentsListPage'
import MetricsLibraryPage from 'components/experiments-v2/MetricsLibraryPage'
import Tabs from 'components/navigation/TabMenu/Tabs'
import TabItem from 'components/navigation/TabMenu/TabItem'

const ExperimentsPage: FC = () => {
  return (
    <div className='app-container container'>
      <Tabs theme='pill' uncontrolled urlParam='experimentsTab'>
        <TabItem tabLabel='Experiments'>
          <ExperimentsListPage />
        </TabItem>
        <TabItem tabLabel='Metrics'>
          <MetricsLibraryPage />
        </TabItem>
      </Tabs>
    </div>
  )
}

export default ExperimentsPage
