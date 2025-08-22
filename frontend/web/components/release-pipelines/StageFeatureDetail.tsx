import classNames from 'classnames'
import { getProjectFlag } from 'common/services/useProjectFlag'
import { getStore } from 'common/store'
import { Features, ProjectFlag } from 'common/types/responses'
import moment from 'moment'
import { useCallback, useEffect, useState } from 'react'
import { useHistory } from 'react-router-dom'

type StageFeatureDetailProps = {
  features: Features | number[]
  projectId: number
  environmentKey?: string
}

const StageFeatureDetail = ({
  environmentKey,
  features,
  projectId,
}: StageFeatureDetailProps) => {
  const history = useHistory()

  const featureIds = Array.isArray(features)
    ? features
    : Object.keys(features || {}).map(Number)
  const [projectFlags, setProjectFlags] = useState<ProjectFlag[]>([])

  const getProjectFlags = useCallback(async () => {
    if (!featureIds.length) {
      return
    }

    try {
      const res = await Promise.all(
        featureIds.map((id) =>
          getProjectFlag(getStore(), {
            id: `${id}`,
            project: projectId,
          }),
        ),
      )
      const projectFlags = res.map((r) => r.data)
      setProjectFlags(projectFlags)
    } catch (error) {
      console.error(error)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [featureIds?.join(','), projectId])

  useEffect(() => {
    getProjectFlags()
  }, [getProjectFlags])

  if (!featureIds.length) {
    return (
      <>
        <h6>Features (0)</h6>
        <p className='text-muted'>No features at this stage.</p>
      </>
    )
  }

  const handleFeatureClick = (flag: ProjectFlag) => {
    if (!environmentKey || !flag.id || !projectId) {
      return
    }

    history.push(
      `/project/${projectId}/environment/${environmentKey}/features?feature=${flag.id}&tab=value`,
    )
  }

  const calculateAmountRemaining = (feature: Features[number]) => {
    if (!feature.phased_rollout_state) {
      return ''
    }

    const partsRemaining =
      (100 - feature.phased_rollout_state.current_split) /
      feature.phased_rollout_state.increase_by
    const duration = moment.duration(
      feature.phased_rollout_state.increase_every,
    )
    const part = moment.duration(duration.asMilliseconds() * partsRemaining)
    return (
      <div className='mt-1'>
        <div className='text-muted text-small'>
          Rollout currently at {feature.phased_rollout_state.current_split}%
        </div>
        <div className='text-muted text-small'>
          {part.humanize()} remaining for complete rollout
        </div>
      </div>
    )
  }

  return (
    <>
      <h6>Features ({featureIds.length})</h6>
      {projectFlags?.map((flag) => (
        <div key={flag.id}>
          <b
            className={classNames('text-muted', {
              'cursor-pointer': !!environmentKey,
            })}
            onClick={() => handleFeatureClick(flag)}
          >
            {flag.name}
          </b>
          {!Array.isArray(features) &&
            features[flag.id]?.phased_rollout_state && (
              <div>{calculateAmountRemaining(features[flag.id])}</div>
            )}
        </div>
      ))}
    </>
  )
}

export default StageFeatureDetail
