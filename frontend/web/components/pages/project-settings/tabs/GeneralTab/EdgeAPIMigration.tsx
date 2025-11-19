import React, { FC } from 'react'
import Icon from 'components/Icon'
import { Project } from 'common/types/responses'
import { useMigrateProjectMutation } from 'common/services/useProject'
import Utils from 'common/utils/utils'

type EdgeAPIMigrationProps = {
  project: Project
}

export const EdgeAPIMigration: FC<EdgeAPIMigrationProps> = ({ project }) => {
  const [migrateProject, { isLoading: isMigrating }] =
    useMigrateProjectMutation()

  const handleMigrate = () => {
    openConfirm({
      body: 'This will migrate your project to the Global Edge API.',
      onYes: async () => {
        await migrateProject({ id: String(project.id) })
      },
      title: 'Migrate to Global Edge API',
    })
  }

  if (Utils.getIsEdge() || !Utils.isSaas()) {
    return null
  }

  return (
    <FormGroup className='mt-4'>
      <Row className='mb-2'>
        <h5 className='mb-0 mr-3'>Global Edge API Opt in</h5>
        <Button
          disabled={isMigrating || Utils.isMigrating()}
          onClick={handleMigrate}
          size='xSmall'
          theme='outline'
        >
          {isMigrating || Utils.isMigrating()
            ? 'Migrating to Edge'
            : 'Start Migration'}{' '}
          <Icon name='arrow-right' width={16} fill='#6837FC' />
        </Button>
      </Row>
      <p className='fs-small lh-sm'>
        Migrate your project onto our Global Edge API. Existing Core API
        endpoints will continue to work whilst the migration takes place. Find
        out more{' '}
        <a
          target='_blank'
          href='https://docs.flagsmith.com/advanced-use/edge-api'
          className='btn-link'
          rel='noreferrer'
        >
          here
        </a>
        .
      </p>
    </FormGroup>
  )
}
