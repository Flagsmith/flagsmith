import { FC, useState } from 'react'
import IdentitySelect from 'components/IdentitySelect';
import Utils from 'common/utils/utils';

type CompareIdentitiesType = {
}

const CompareIdentities: FC<CompareIdentitiesType> = ({}) => {
  const [leftId, setLeftId] = useState()
  const [rightId, setRightId] = useState()
  const [environmentId, setEnvironmentId] = useState();

    const isEdge = Utils.getIsEdge()
  return <>
      <EnvironmentSelect
  <IdentitySelect value={leftId} isEdge={} onChange={} environmentId={}
  </>
}

export default CompareIdentities
