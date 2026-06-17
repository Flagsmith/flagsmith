import { FC } from 'react'
import Icon from 'components/icons/Icon'
import ContentCard from 'components/base/grid/ContentCard'

const AudienceStep: FC = () => {
  return (
    <div className='d-flex flex-column gap-4'>
      <ContentCard
        title='Targeting'
        description='Define who is eligible for the experiment using attribute conditions. Conditions are AND-joined. Leave empty to run on all identities in the environment. Conditions are frozen at launch. Later edits to existing Segments cannot drift the experiment audience.'
      >
        <div className='d-flex align-items-start gap-3 p-3 border rounded'>
          <Icon
            name='people'
            width={24}
            fill='currentColor'
            className='text-muted flex-shrink-0 mt-1'
          />
          <div>
            <div className='fw-bold'>All identities in this environment</div>
            <div className='text-muted fs-small'>
              No targeting conditions. Every identity is eligible for the
              experiment. Add a condition to filter the audience.
            </div>
          </div>
        </div>
      </ContentCard>
    </div>
  )
}

export default AudienceStep
