import React, { FC, useEffect, useMemo, useState } from 'react'
import IdentitySelect, { IdentitySelectType } from './IdentitySelect'
import Utils from 'common/utils/utils'
import EnvironmentSelect from './EnvironmentSelect'
import { useGetIdentityFeatureStatesQuery } from 'common/services/useIdentityFeatureState'
import { useGetProjectFlagsQuery } from 'common/services/useProjectFlag'
import Tag from './tags/Tag'
import PanelSearch from './PanelSearch'
import { ProjectFlag, Res } from 'common/types/responses'
import Icon from './Icon'
import Switch from './Switch'
import FeatureValue from './FeatureValue'
import { sortBy } from 'lodash'
import { useHasPermission } from 'common/providers/Permission'
import Constants from 'common/constants'

type CompareIdentitiesType = {
  projectId: string
  environmentId: string
}
const selectWidth = 300
const featureNameWidth = 300

const calculateFeatureDifference = (
  projectFlagId: number,
  leftUser: Res['identityFeatureStates'] | undefined,
  rightUser: Res['identityFeatureStates'] | undefined,
) => {
  const featureStateLeft = leftUser?.find((v) => v.feature.id === projectFlagId)
  const featureStateRight = rightUser?.find(
    (v) => v.feature.id === projectFlagId,
  )
  const enabledDifferent =
    featureStateLeft?.enabled !== featureStateRight?.enabled
  const valueDifferent =
    featureStateLeft?.feature_state_value !==
    featureStateRight?.feature_state_value

  return {
    enabledDifferent,
    featureStateLeft,
    featureStateRight,
    valueDifferent,
  }
}
const CompareIdentities: FC<CompareIdentitiesType> = ({
  environmentId: _environmentId,
  projectId,
}) => {
  const [leftId, setLeftId] = useState<IdentitySelectType['value']>()
  const [rightId, setRightId] = useState<IdentitySelectType['value']>()
  const { data: projectFlags } = useGetProjectFlagsQuery({ project: projectId })
  const [environmentId, setEnvironmentId] = useState(_environmentId)
  const [showArchived, setShowArchived] = useState(false)

  const { isLoading: permissionLoading, permission } = useHasPermission({
    id: environmentId,
    level: 'environment',
    permission: Utils.getViewIdentitiesPermission(),
  })

  const { data: leftUser } = useGetIdentityFeatureStatesQuery(
    { environment: environmentId, user: `${leftId?.value}` },
    { skip: !leftId },
  )
  const { data: rightUser } = useGetIdentityFeatureStatesQuery(
    { environment: environmentId, user: `${rightId?.value}` },
    { skip: !rightId },
  )

  useEffect(() => {
    // Clear users whenever environment or project is changed
    setLeftId(null)
    setRightId(null)
  }, [environmentId, projectId])

  const filteredItems = useMemo(() => {
    if (!projectFlags?.results) return projectFlags?.results

    return sortBy(
      projectFlags.results.filter((v) => {
        if (showArchived) {
          return true
        }
        return !v.is_archived
      }),
      (projectFlag) => {
        const { id, name } = projectFlag
        const { enabledDifferent, valueDifferent } = calculateFeatureDifference(
          id,
          leftUser,
          rightUser,
        )
        const isDifferent = enabledDifferent || valueDifferent ? 0 : 1
        return `${isDifferent}${name}`
      },
    )
  }, [projectFlags, showArchived, leftUser, rightUser])

  const isReady =
    !!leftId && !!rightId && !!leftUser && !!rightUser && !!projectFlags

  const isEdge = Utils.getIsEdge()

  const goUser = (user: IdentitySelectType['value'], feature: string) => {
    window.open(
      `${
        document.location.origin
      }/project/${projectId}/environment/${environmentId}/users/${encodeURIComponent(
        user!.label,
      )}/${user!.value}?flag=${encodeURIComponent(feature)}`,
      '_blank',
    )
  }

  return (
    <div>
      <h3>Compare Identities</h3>
      <p>Compare feature states between 2 identities</p>
      <div className='mb-2' style={{ width: selectWidth }}>
        <EnvironmentSelect
          value={environmentId}
          projectId={projectId}
          onChange={(v) => {
            setRightId(null)
            setLeftId(null)
            setEnvironmentId(v)
          }}
        />
      </div>
      {!permission && !permissionLoading ? (
        <div
          dangerouslySetInnerHTML={{
            __html: Constants.environmentPermissions('View Identities'),
          }}
        />
      ) : (
        <Row>
          <div className='mr-2' style={{ width: selectWidth }}>
            <IdentitySelect
              value={leftId}
              isEdge={isEdge}
              ignoreIds={[`${rightId?.value}`]}
              onChange={setLeftId}
              environmentId={environmentId}
            />
          </div>
          <div>
            <span className='icon ios ion-md-arrow-back mx-2' />
          </div>
          <div className='mr-2' style={{ width: selectWidth }}>
            <IdentitySelect
              value={rightId}
              ignoreIds={[`${leftId?.value}`]}
              isEdge={isEdge}
              onChange={setRightId}
              environmentId={environmentId}
            />
          </div>
        </Row>
      )}

      {isReady && (
        <>
          <PanelSearch
            title={'Changed Flags'}
            searchPanel={
              <Row className='mb-2'>
                <Tag
                  selected={showArchived}
                  onClick={() => {
                    setShowArchived(!showArchived)
                  }}
                  className='px-2 py-2 ml-2 mr-2'
                  tag={{ color: '#0AADDF', label: 'Archived' }}
                />
              </Row>
            }
            items={filteredItems}
            renderRow={(data: ProjectFlag) => {
              const { description, id, name } = data
              const {
                enabledDifferent,
                featureStateLeft,
                featureStateRight,
                valueDifferent,
              } = calculateFeatureDifference(id, leftUser, rightUser)
              const goUserLeft = () => {
                goUser(leftId, data.name)
              }
              const goUserRight = () => {
                goUser(leftId, data.name)
              }

              return (
                <Flex className={'flex-row list-item'}>
                  <div
                    style={{ width: featureNameWidth }}
                    className={`table-column ${
                      !enabledDifferent && !valueDifferent && 'faded'
                    }`}
                  >
                    <span className='font-weight-medium'>
                      {description ? (
                        <Tooltip
                          title={
                            <span>
                              {name}
                              <span className={'ms-1'}></span>
                              <Icon name='info-outlined' />
                            </span>
                          }
                        >
                          {description}
                        </Tooltip>
                      ) : (
                        name
                      )}
                    </span>
                  </div>
                  <div
                    onClick={goUserLeft}
                    className={`table-column ${!enabledDifferent && 'faded'}`}
                    style={{ width: '120px' }}
                  >
                    <Switch checked={featureStateLeft?.enabled} />
                  </div>
                  <Flex
                    onClick={goUserLeft}
                    className={`table-column ${!valueDifferent && 'faded'}`}
                  >
                    {featureStateLeft && (
                      <FeatureValue
                        includeEmpty={false}
                        value={featureStateLeft?.feature_state_value}
                      />
                    )}
                  </Flex>
                  <div
                    onClick={goUserRight}
                    className={`table-column ${!enabledDifferent && 'faded'}`}
                    style={{ width: '120px' }}
                  >
                    <Switch checked={featureStateRight?.enabled} />
                  </div>
                  <Flex
                    onClick={goUserRight}
                    className={`table-column ${!valueDifferent && 'faded'}`}
                  >
                    {featureStateRight && (
                      <FeatureValue
                        includeEmpty={false}
                        value={featureStateRight?.feature_state_value}
                      />
                    )}
                  </Flex>
                </Flex>
              )
            }}
            header={
              <Row className='table-header'>
                <div
                  className='table-column px-3'
                  style={{ width: featureNameWidth }}
                >
                  Name
                </div>
                <Flex className='flex-row'>
                  <div className='table-column' style={{ width: '120px' }}>
                    {leftId?.label}
                  </div>
                  <Flex className='table-column'></Flex>
                </Flex>
                <Flex className='flex-row'>
                  <div className='table-column' style={{ width: '120px' }}>
                    {rightId?.label}
                  </div>
                  <Flex className='table-column'></Flex>
                </Flex>
              </Row>
            }
          />
        </>
      )}
    </div>
  )
}

export default CompareIdentities
