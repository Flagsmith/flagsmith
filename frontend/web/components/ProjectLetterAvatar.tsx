import React, { FC } from 'react'
import Utils from 'common/utils/utils'

type ProjectLetterAvatarProps = {
  name: string
  index: number
}

const ProjectLetterAvatar: FC<ProjectLetterAvatarProps> = ({ index, name }) => (
  <span
    aria-hidden='true'
    style={{ backgroundColor: Utils.getProjectColour(index) }}
    className='btn-project-letter mb-0'
  >
    {name[0]}
  </span>
)

export default ProjectLetterAvatar
