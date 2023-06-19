import React, { FC, useEffect, useState } from 'react'
import IdentitySelect, { IdentitySelectType } from './IdentitySelect'
import Utils from 'common/utils/utils'
import EnvironmentSelect from './EnvironmentSelect'

type CompareIdentitiesType = {
  projectId: string
  environmentId: string
}
const selectWidth = 300

const CompareIdentities: FC<CompareIdentitiesType> = ({
  environmentId: _environmentId,
  projectId,
}) => {
  const [leftId, setLeftId] = useState<IdentitySelectType['value']>()
  const [rightId, setRightId] = useState<IdentitySelectType['value']>()
  const [environmentId, setEnvironmentId] = useState(_environmentId)
  const isReady = !!rightId && leftId
  useEffect(() => {
    setLeftId(null)
    setRightId(null)
  }, [environmentId])

  const isEdge = Utils.getIsEdge()
  return (
    <div>
      <h3>Compare Identities</h3>
      <p>Compare feature states between 2 identities</p>
      <div className='mb-2' style={{ width: selectWidth }}>
        <EnvironmentSelect
          value={environmentId}
          projectId={projectId}
          onChange={setEnvironmentId}
        />
      </div>
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
      {isReady && <div>Hi</div>}
    </div>
  )
}

export default CompareIdentities
