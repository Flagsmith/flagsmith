import React, { FC } from 'react'
import InfoMessage from './InfoMessage'
import flagsmith from 'flagsmith'

type AnnouncementPerPageValueType = {
  id: string
  title: string
  description: string
  isClosable: boolean
  buttonText: string
  url: string
}

type AnnouncementPerPageType = {
  announcementPerPageValue: AnnouncementPerPageValueType
}

const AnnouncementPerPage: FC<AnnouncementPerPageType> = ({
  announcementPerPageValue,
}) => {
  const { buttonText, description, id, isClosable, title, url } =
    announcementPerPageValue
  const closeAnnouncement = (id: string) => {
    flagsmith.setTrait(`dismissed_announcement_per_page`, id)
  }

  return (
    <div className='container mt-4'>
      <div className='row'>
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
      </div>
    </div>
  )
}

export default AnnouncementPerPage
