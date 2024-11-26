import React, { FC, useMemo } from 'react'
import { ChangeRequest } from 'common/types/responses'
import { useGetFeatureStatesQuery } from 'common/services/useFeatureState'
import DiffFeature from './DiffFeature'
import { mergeChangeSets } from 'common/services/useChangeRequest'
import DiffSegment from './DiffSegment'
import Tabs from "components/base/forms/Tabs";
import TabItem from "components/base/forms/TabItem";

type DiffChangeRequestType = {
  changeRequest: ChangeRequest | null
  feature: number
  projectId: string
  environmentId: string
  isVersioned: boolean
}
const DiffChangeRequest: FC<DiffChangeRequestType> = ({
  changeRequest,
  environmentId,
  feature,
  isVersioned,
  projectId,
}) => {
  const { data, isLoading } = useGetFeatureStatesQuery(
    {
      environment: changeRequest?.environment,
      feature,
    },
    { refetchOnMountOrArgChange: true, skip: !changeRequest },
  )

  const newState = useMemo(() => {
    const changeSets = changeRequest?.change_sets?.filter(
      (v) => v.feature === feature,
    )
    if (!changeSets?.length) {
      return changeRequest?.feature_states
    }
    return mergeChangeSets(changeSets, data?.results, changeRequest?.conflicts)
  }, [changeRequest, feature, data])

  if (!changeRequest) {
    return null
  }

  if (isLoading) {
    return (
      <div className='text-center'>
        <Loader />
      </div>
    )
  }

  return (
        <DiffSegment
          oldSegment={{
            'created_at': null,
            'deleted_at': null,
            'description': 'Internal users',
            'feature': null,
            'id': 2051,
            'metadata': [],
            'name': 'flagsmith_team',
            'project': 12,
            'rules': [
              {
                'conditions': [],
                'id': 25189,
                'rules': [
                  {
                    'conditions': [
                      {
                        'description': null,
                        'id': 51385,
                        'operator': 'REGEX',
                        'property': 'email',
                        'value': '.*@flagsmith\\.com',
                      },
                    ],
                    'id': 25190,
                    'rules': [],
                    'type': 'ANY',
                  },
                ],
                'type': 'ALL',
              },
            ],
            'updated_at': '2024-08-27T08:39:23.481648Z',
            'uuid': '903dce22-e9e0-4be8-91d3-30ede78c6224',
            'version': 3,
            'version_of': 2051,
          }}
          newSegment={{
            'deleted_at': null,
            'created_at': null,
            'description': 'Internal users',
            'id': 2051,
            'metadata': [],
            'feature': null,
            'name': 'flagsmith_team',
            'project': 12,
            'rules': [
              {
                'id': 25189,
                'rules': [
                  {
                    'id': 25190,
                    'rules': [],
                    'type': 'ANY',
                    'conditions': [
                      {
                        'id': 51385,
                        'operator': 'REGEX',
                        'property': 'email',
                        'description': null,
                        'value': '.*@flagsmith2\\.com',
                      },
                    ],
                  },
                  {
                    'id': 25191,
                    'rules': [],
                    'type': 'ANY',
                    'conditions': [
                      {
                        'id': 51385,
                        'operator': 'REGEX',
                        'property': 'email',
                        'description': null,
                        'value': 'kyle@bla\\.com',
                      },
                    ],
                  },
                  {
                    'id': 251902,
                    'rules': [],
                    'type': 'NONE',
                    'conditions': [
                      {
                        'id': 51385,
                        'operator': 'REGEX',
                        'property': 'email',
                        'description': null,
                        'value': '.*@bla\\.com',
                      },
                    ],
                  },
                ],
                'conditions': [],
                'type': 'ALL',
              },
            ],
            'updated_at': '2024-08-27T08:39:23.481648Z',
            'uuid': '903dce22-e9e0-4be8-91d3-30ede78c6224',
            'version': 3,
            'version_of': 2051,
          }}
        />
  )

  return (
    <DiffFeature
      conflicts={changeRequest.conflicts}
      environmentId={environmentId}
      featureId={feature}
      disableSegments={!isVersioned}
      projectId={projectId}
      newState={newState || []}
      oldState={data?.results || []}
    />
  )
}

export default DiffChangeRequest
