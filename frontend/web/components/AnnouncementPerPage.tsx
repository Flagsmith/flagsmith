import React, { FC } from 'react'
import InfoMessage from './InfoMessage'
import flagsmith from 'flagsmith'
import Utils from 'common/utils/utils'
import { AnnouncementValueType } from './Announcement'

type AnnouncementPerPageValueType = AnnouncementValueType & {
  pages: string[]
}

type AnnouncementPerPageType = { pathname: string }

const AnnouncementPerPage: FC<AnnouncementPerPageType> = ({ pathname }) => {
  const closeAnnouncement = (id: string) => {
    flagsmith.setTrait(`dismissed_announcement_per_page`, id)
  }

  const announcementPerPageDismissed = flagsmith.getTrait(
    'dismissed_announcement_per_page',
  )
  const announcementPerPageValue = Utils.getFlagsmithJSONValue(
    'announcement_per_page',
    null,
  ) as AnnouncementPerPageValueType

  const showAnnouncementPerPage =
    (!announcementPerPageDismissed ||
      announcementPerPageDismissed !== announcementPerPageValue.id) &&
    Utils.getFlagsmithHasFeature('announcement_per_page') &&
    announcementPerPageValue?.pages?.length > 0

  const announcementInPage = announcementPerPageValue?.pages?.some((page) =>
    pathname.includes(page),
  )
  return (
    <>
      {showAnnouncementPerPage && announcementInPage && (
        <InfoMessage
          title={announcementPerPageValue?.title}
          isClosable={announcementPerPageValue?.isClosable}
          close={() => closeAnnouncement(announcementPerPageValue?.id)}
          buttonText={announcementPerPageValue?.buttonText}
          url={announcementPerPageValue?.url}
        >
          <div>
            <div>{announcementPerPageValue?.description}</div>
          </div>
        </InfoMessage>
      )}
    </>
  )
}

export default AnnouncementPerPage
