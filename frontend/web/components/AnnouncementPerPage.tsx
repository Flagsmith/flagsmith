import { get } from 'lodash'
import React, { FC } from 'react'
import InfoMessage from './InfoMessage'
import flagsmith from 'flagsmith'
import Utils from 'common/utils/utils'
import { AnnouncementValueType } from './Announcement'
import { matchPath } from 'react-router'
import { routes } from 'web/routes'

type AnnouncementPerPageValueType = AnnouncementValueType & {
  pages: string[]
  projectId: number
  params: { [key: string]: string }
}

type AnnouncementPerPageType = {
  pathname: string
}

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

  const announcementInPage = announcementPerPageValue?.pages?.some((page) => {
    if (Object.keys(routes).includes(page)) {
      const match = matchPath(pathname, {
        exact: false,
        path: routes[page],
        strict: false,
      })

      if (match) {
        const annParams = announcementPerPageValue?.params || {}
        const matchParams = match?.params || {}
        const objectsMatch = (
          obj1: AnnouncementPerPageValueType['params'],
          obj2: AnnouncementPerPageValueType['params'],
        ) => {
          return Object.keys(obj2).every((key) => {
            if (Array.isArray(obj2[key])) {
              return obj2[key].some((item) => {
                return `${item}` === `${obj1[key]}`
              })
            } else {
              return `${obj1[key]}` === `${obj2[key]}`
            }
          })
        }
        const matchParamsMatch = objectsMatch(matchParams, annParams)
        if (matchParamsMatch) {
          return true
        }

        return false
      }
    }

    return false
  })

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
