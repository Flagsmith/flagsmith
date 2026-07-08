import React, { FC } from 'react'
import { useGetFeatureStatesQuery } from 'common/services/useFeatureState'
import { FeatureStateWithConflict } from 'common/types/responses'
import DiffFeature from 'components/diff/DiffFeature'
import { FeatureChange } from './types'

type ExpandedRowProps = {
  item: FeatureChange
  projectId: string
  environmentLeftId: number
  environmentRightId: number
  oldEnvName?: string
  newEnvName?: string
}

const ExpandedRow: FC<ExpandedRowProps> = ({
  environmentLeftId,
  environmentRightId,
  item,
  newEnvName,
  oldEnvName,
  projectId,
}) => {
  const { data: leftStates, isLoading: leftLoading } = useGetFeatureStatesQuery(
    {
      environment: environmentLeftId,
      feature: item.projectFlagLeft.id,
    },
  )

  const { data: rightStates, isLoading: rightLoading } =
    useGetFeatureStatesQuery({
      environment: environmentRightId,
      feature: item.projectFlagLeft.id,
    })

  if (leftLoading || rightLoading) {
    return (
      <div className='p-4 text-center'>
        <Loader />
      </div>
    )
  }

  return (
    <div className='px-4 py-3 bg-light200'>
      <DiffFeature
        featureId={item.projectFlagLeft.id}
        projectId={projectId}
        environmentId={String(environmentRightId)}
        oldState={
          (leftStates?.results || []) as unknown as FeatureStateWithConflict[]
        }
        newState={
          (rightStates?.results || []) as unknown as FeatureStateWithConflict[]
        }
        oldEnvName={oldEnvName}
        newEnvName={newEnvName}
        noChangesMessage='No differences between environments'
        tabTheme='pill'
      />
    </div>
  )
}

export default ExpandedRow
