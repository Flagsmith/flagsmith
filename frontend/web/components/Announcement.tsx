import React, { FC } from 'react'
import InfoMessage from './InfoMessage'
import flagsmith from 'flagsmith'
import Utils from 'common/utils/utils'

export type AnnouncementValueType = {
  id: string
  title: string
  description: string
  isClosable: boolean
  buttonText: string
  url: string
}

type AnnouncementType = {}

const Announcement: FC<AnnouncementType> = () => {
  const closeAnnouncement = (id: string) => {
    flagsmith.setTrait(`dismissed_announcement`, id)
  }

  const announcementValue = Utils.getFlagsmithJSONValue('announcement', null)

  if (!announcementValue) {
    return null
  }

  const { buttonText, description, id, isClosable, title, url } =
    announcementValue as AnnouncementValueType
  const dismissed = flagsmith.getTrait('dismissed_announcement')

  const showBanner =
    announcementValue &&
    (!dismissed || dismissed !== announcementValue.id) &&
    Utils.getFlagsmithHasFeature('announcement')

  return (
    <>
      {showBanner && (
        <InfoMessage
          title={title}
          isClosable={isClosable}
          close={() => closeAnnouncement(id)}
          buttonText={buttonText}
          url={url}
        >
          <div>
            <div>{description}</div>
          </div>
        </InfoMessage>
      )}
    </>
  )
}

export default Announcement
