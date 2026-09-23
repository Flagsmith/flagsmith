import React, { FC, useState } from 'react'
import Tabs from 'components/navigation/TabMenu/Tabs'
import TabItem from 'components/navigation/TabMenu/TabItem'
import UsageTab from 'components/modals/create-feature/tabs/UsageTab'
import FeatureSettingsTab from 'components/modals/create-feature/tabs/FeatureSettingsTab'
import type { ProjectFlag } from 'common/types/responses'

type FeatureUsageModalProps = {
  projectId: number | string
  environmentId: number
  projectFlag: ProjectFlag
}

const FeatureUsageModal: FC<FeatureUsageModalProps> = ({
  environmentId,
  projectFlag,
  projectId,
}) => {
  const [localProjectFlag, setLocalProjectFlag] =
    useState<ProjectFlag>(projectFlag)

  return (
    <Tabs>
      <TabItem tabLabel='Usage'>
        <UsageTab
          projectId={projectId}
          featureId={projectFlag.id}
          environmentId={environmentId}
        />
      </TabItem>
      <TabItem tabLabel='Settings'>
        <FeatureSettingsTab
          projectId={projectId}
          projectFlag={localProjectFlag}
          onChange={setLocalProjectFlag}
          onHasMetadataRequiredChange={() => {}}
        />
      </TabItem>
    </Tabs>
  )
}

export default FeatureUsageModal
