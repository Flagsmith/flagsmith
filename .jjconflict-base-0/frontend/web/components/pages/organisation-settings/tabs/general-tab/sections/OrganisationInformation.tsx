import React, { FormEvent, useState } from 'react'
import { Organisation } from 'common/types/responses'
import { useUpdateOrganisationWithToast } from 'components/pages/organisation-settings/hooks'
import Utils from 'common/utils/utils'

type OrganisationInformationProps = {
  organisation: Organisation
}

export const OrganisationInformation = ({
  organisation,
}: OrganisationInformationProps) => {
  const [updateOrganisationWithToast, { isLoading: isSaving }] =
    useUpdateOrganisationWithToast()
  const [name, setName] = useState(organisation.name)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!name || isSaving) return

    await updateOrganisationWithToast({ name }, organisation.id, {
      errorMessage: 'Failed to save organisation. Please try again.',
      successMessage: 'Saved organisation',
    })
  }

  return (
    <FormGroup>
      <form onSubmit={handleSubmit} className='d-flex flex-column gap-2 m-0'>
        <Row>
          <Flex>
            <InputGroup
              title='Organisation Name'
              value={name}
              inputClassName='input--wide'
              name='organisation-name'
              data-test='organisation-name'
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                setName(Utils.safeParseEventValue(e))
              }
              isValid={!!name && name.length > 0}
              type='text'
              placeholder='My Organisation'
              inputProps={{
                className: 'full-width',
              }}
            />
          </Flex>

          <Button
            type='submit'
            id='save-org-btn'
            data-test='save-org-btn'
            disabled={isSaving || !name}
            className='ml-3'
          >
            {isSaving ? 'Updating' : 'Update Name'}
          </Button>
        </Row>
      </form>
    </FormGroup>
  )
}
