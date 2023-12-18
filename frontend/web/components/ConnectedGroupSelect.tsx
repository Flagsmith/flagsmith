import React, { FC } from 'react'
import GroupSelect, { GroupSelectType } from './GroupSelect'
import { useGetGroupSummariesQuery } from 'common/services/useGroupSummary'
import { IonIcon } from '@ionic/react'
import { close } from 'ionicons/icons' // we need this to make JSX compile

type ConnectedGroupSelectType = GroupSelectType & {
  orgId: string
  showValues?: boolean
}

const ConnectedGroupSelect: FC<ConnectedGroupSelectType> = ({
  orgId,
  showValues,
  ...props
}) => {
  const { data } = useGetGroupSummariesQuery({ orgId })
  return (
    <>
      {!!showValues && (
        <Row style={{ rowGap: '12px' }}>
          {props?.value?.map((u) => {
            const group = data?.find((v) => v.id === u)
            if (!group) return null
            return (
              <Row
                onClick={() => props.onRemove(u, false)}
                key={u}
                className='chip mr-2'
              >
                <span className='font-weight-bold'>{group.name}</span>
                <span className='chip-icon ion'>
                  <IonIcon icon={close} />
                </span>
              </Row>
            )
          })}
          {!props.value?.length && <div>This flag has no assigned groups</div>}
        </Row>
      )}
      <GroupSelect {...props} onRemove={props.onRemove} groups={data} />
    </>
  )
}

export default ConnectedGroupSelect
