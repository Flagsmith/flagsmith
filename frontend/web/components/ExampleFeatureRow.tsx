import React, { FC } from 'react'
import { FeatureState, ProjectFlag } from 'common/types/responses'
import { useGetTagsQuery } from 'common/services/useTag'
import FeatureRow from './FeatureRow'
import { flag } from 'ionicons/icons'

type ExampleFeatureRowType = {}

const ExampleFeatureRow: FC<ExampleFeatureRowType> = ({}) => {
  const flag: ProjectFlag = {
    created_date: new Date().toISOString(),
    default_enabled: true,
    description: 'Feature description',
    id: 1,
    initial_value: 'Blue',
    is_archived: false,
    is_server_key_only: false,
    multivariate_options: [],
    name: 'example_feature',
    num_identity_overrides: 1,
    num_segment_overrides: 1,
    owner_groups: [],
    owners: [],
    project: 1,
    tags: [],
    type: 'STANDARD',
    uuid: '1',
  }
  const flag2: ProjectFlag = {
    created_date: new Date().toISOString(),
    default_enabled: true,
    description: 'Feature description',
    id: 1,
    initial_value: `2`,
    is_archived: false,
    is_server_key_only: false,
    multivariate_options: [],
    name: 'example_feature2',
    num_identity_overrides: 1,
    num_segment_overrides: 1,
    owner_groups: [],
    owners: [],
    project: 1,
    tags: [],
    type: 'STANDARD',
    uuid: '1',
  }
  const featureState: FeatureState = {
    created_at: '',
    enabled: false,
    environment: 1,
    feature: flag.id,
    feature_state_value: flag.initial_value,
    id: 1,
    multivariate_feature_state_values: [],
    updated_at: '',
    uuid: '',
  }
  return (
    <div className='panel no-pad'>
      <div className='panel-content'>
        <div className='search-list'>
          <FeatureRow
            environmentFlags={{ 1: featureState }}
            projectFlags={[flag, flag2]}
            environmentId={1}
            disableControls
            permission={true}
            projectId={'2'}
            index={0}
            toggleFlag={() => {}}
            removeFlag={() => {}}
            projectFlag={flag}
          />
          <FeatureRow
            environmentFlags={{ 1: featureState }}
            projectFlags={[flag, flag2]}
            environmentId={1}
            disableControls
            permission={true}
            projectId={'2'}
            index={1}
            toggleFlag={() => {}}
            removeFlag={() => {}}
            projectFlag={flag}
          />
        </div>
      </div>
    </div>
  )
}

export default ExampleFeatureRow
