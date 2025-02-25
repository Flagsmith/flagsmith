import AppActions from 'common/dispatcher/app-actions'
import AccountProvider from 'common/providers/AccountProvider'
import Utils from 'common/utils/utils'
import Button from 'components/base/forms/Button'
import InputGroup from 'components/base/forms/InputGroup'
import API from 'project/api'
import { FC, useState } from 'react'
import Project from 'common/project'

const CreateOrganisationModal: FC = () => {
  const [name, setName] = useState('')

  const onSave = (id: any) => {
    AppActions.selectOrganisation(id)
    AppActions.getOrganisation(id)
    API.setCookie('organisation', `${id}`)
  }

  return (
    <div className='p-4'>
      <AccountProvider onSave={onSave}>
        {(
          { isSaving }: { isSaving: boolean },
          { createOrganisation }: { createOrganisation: (name: any) => void },
        ) => (
          <form
            onSubmit={(e) => {
              e.preventDefault()
              if (Project.capterraKey) {
                const parts = Project.capterraKey.split(',')
                Utils.appendImage(
                  `https://ct.capterra.com/capterra_tracker.gif?vid=${parts[0]}&vkey=${parts[1]}`,
                )
              }
              createOrganisation(name)
              closeModal()
            }}
          >
            <InputGroup
              inputProps={{ className: 'full-width', name: 'orgName' }}
              title='Organisation Name'
              placeholder='E.g. ACME Ltd'
              onChange={(e: React.FormEvent<HTMLInputElement>) =>
                setName(Utils.safeParseEventValue(e))
              }
              className='mb-5'
            />
            <div className='text-right'>
              <Button
                type='submit'
                disabled={isSaving || !name}
                id='create-org-btn'
              >
                Create Organisation
              </Button>
            </div>
          </form>
        )}
      </AccountProvider>
    </div>
  )
}

export default CreateOrganisationModal
