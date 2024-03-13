import React, { FC } from 'react'
import { Tag as TTag } from 'common/types/responses'
import Icon from 'components/Icon'
import color from 'color'
import Format from 'common/utils/format'
import { IonIcon } from '@ionic/react'
import { lockClosed } from 'ionicons/icons'
import Tooltip from 'components/Tooltip'

type TagContent = {
  tag: Partial<TTag>
  truncateTo?: Number
}

const TagContent: FC<TagContent> = ({ tag, truncateTo }) => {
  let tagLabel = tag.label
  if (truncateTo) {
    tagLabel = Format.truncateText(tagLabel, truncateTo)
  }

  if (!tagLabel) {
    return null
  }
  return (
    <span className={'mr-1 flex-row align-items-center'}>
      {tagLabel}
      {tag.is_system_tag && (
        <Tooltip
          titleClassName='d-flex'
          plainText
          title={
            <IonIcon
              className='ms-1'
              icon={lockClosed}
              color={color(tag.color).darken(0.1).string()}
            />
          }
        >
          {'System generated tag'}
        </Tooltip>
      )}
      {tag.is_permanent && (
        <Tooltip
          titleClassName='d-flex'
          plainText
          title={
            <IonIcon
              className='ms-1'
              icon={lockClosed}
              color={color(tag.color).darken(0.1).string()}
            />
          }
        >
          Permanent tag
        </Tooltip>
      )}
    </span>
  )
}

export default TagContent
