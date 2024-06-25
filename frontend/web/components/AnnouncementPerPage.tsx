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

  const { buttonText, description, id, isClosable, pages, title, url } =
    announcementPerPageValue

  const showAnnouncementPerPage =
    (!announcementPerPageDismissed ||
      announcementPerPageDismissed !== announcementPerPageValue.id) &&
    Utils.getFlagsmithHasFeature('announcement_per_page') &&
    pages?.length > 0

  const announcementInPage = pages?.some((page) => pathname.includes(page))
  return (
    <>
      {showAnnouncementPerPage && announcementInPage && (
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

export default AnnouncementPerPage
