import React, { FC, useMemo, useState } from 'react'
import ProjectFilter from './ProjectFilter'
import AccountStore from 'common/stores/account-store'
import FlagSelect from './FlagSelect'
import { Project, ProjectFlag } from 'common/types/responses'
import useAllFeatureStates from 'common/services/useAllFeatureStates'
import EnvironmentFilter from './EnvironmentFilter'
import DiffFeature from './diff/DiffFeature'
import DiffString from './diff/DiffString'
import DiffEnabled from './diff/DiffEnabled'
import { getFeatureStateDiff } from './diff/diff-utils'

type CompareProjectsType = {}

const CompareProjects: FC<CompareProjectsType> = ({}) => {
  const [projectLeft, setProjectLeft] = useState<string>()
  const [environmentLeft, setEnvironmentLeft] = useState<string>()
  const [environmentRight, setEnvironmentRight] = useState<string>()
  const [projectRight, setProjectRight] = useState<string>()
  const [projectFlagLeft, setProjectFlagLeft] = useState<
    ProjectFlag | undefined
  >()
  const [projectFlagRight, setProjectFlagRight] = useState<
    ProjectFlag | undefined
  >()

  const featureStatesLeft = useAllFeatureStates({
    featureId: projectFlagLeft?.id,
    projectId: projectLeft,
  })
  const featureStatesRight = useAllFeatureStates({
    featureId: projectFlagRight?.id,
    projectId: projectRight,
  })
  const leftFeatureState =
    environmentLeft &&
    featureStatesLeft?.[environmentLeft]?.environmentFeatureState
  const rightFeatureState =
    environmentRight &&
    featureStatesRight?.[environmentRight]?.environmentFeatureState
  const diff =
    leftFeatureState &&
    rightFeatureState &&
    getFeatureStateDiff(leftFeatureState, rightFeatureState)
  return (
    <>
      <div className='col-md-8'>
        <h5 className='mb-1'>Compare Projects</h5>
        <p className='fs-small mb-4 lh-sm'>
          Shows the feature value of Project A compared to Project B.
        </p>
      </div>
      <div className='row'>
        <div className='col-12'>
          <div className='py-2 fw-bold'>Project A Feature</div>
          <div className='d-flex gap-4'>
            <div style={{ width: 250 }}>
              <ProjectFilter
                exclude={[`${projectRight}`]}
                organisationId={AccountStore.getOrganisation()?.id}
                onChange={setProjectLeft}
                value={projectLeft}
              />
            </div>
            <div style={{ width: 250 }}>
              {!!projectLeft && (
                <FlagSelect
                  value={projectFlagLeft?.id}
                  projectId={projectLeft}
                  onChange={(_, flag) => setProjectFlagLeft(flag)}
                />
              )}
            </div>
            <div style={{ width: 250 }}>
              {!!projectLeft && (
                <EnvironmentFilter
                  value={environmentLeft}
                  projectId={projectLeft}
                  onChange={setEnvironmentLeft}
                />
              )}
            </div>
          </div>
        </div>
      </div>
      <div className='row mt-4'>
        <div className='col-12'>
          <div className='py-2 fw-bold'>Project B Feature</div>
          <div className='d-flex gap-4'>
            <div style={{ width: 250 }}>
              <ProjectFilter
                exclude={[`${projectLeft}`]}
                organisationId={AccountStore.getOrganisation()?.id}
                onChange={setProjectRight}
                value={projectRight}
              />
            </div>
            <div style={{ width: 250 }}>
              {!!projectRight && (
                <FlagSelect
                  value={projectFlagRight?.id}
                  projectId={projectRight}
                  onChange={(_, flag) => setProjectFlagRight(flag)}
                />
              )}
            </div>
            <div style={{ width: 250 }}>
              {!!projectRight && (
                <EnvironmentFilter
                  value={environmentRight}
                  projectId={projectRight}
                  onChange={setEnvironmentRight}
                />
              )}
            </div>
          </div>
        </div>
      </div>
      {!!diff && (
        <div className='panel-content'>
          <div className='search-list mt-2'>
            <div className='flex-row table-header'>
              <div className='table-column flex-row flex flex-1'>Value</div>
              <div className='table-column flex-row text-center'>Enabled</div>
            </div>
            <div className='flex-row pt-4 list-item list-item-sm'>
              <div className='table-column flex flex-1'>
                <div>
                  <DiffString
                    data-test={'version-value'}
                    oldValue={diff.oldValue}
                    newValue={diff.newValue}
                  />
                </div>
              </div>

              <div className='table-column text-center'>
                <DiffEnabled
                  data-test={'version-enabled'}
                  oldValue={diff.oldEnabled}
                  newValue={diff.newEnabled}
                />
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  )
}

export default CompareProjects
