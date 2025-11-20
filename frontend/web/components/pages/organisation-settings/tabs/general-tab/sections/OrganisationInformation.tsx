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
      successMessage: 'Organisation Saved',
    })
  }

  return (
    <FormGroup>
      <form onSubmit={handleSubmit}>
        <Row className='align-items-start'>
          <Flex className='ml-0'>
            <Input
              value={name}
              inputClassName='full-width'
              name='org-name'
              data-test='org-name'
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                setName(Utils.safeParseEventValue(e))
              }
              isValid={!!name && name.length > 0}
              type='text'
              placeholder='My Organisation Name'
            />
          </Flex>
        </Row>

        <div className='text-right'>
          <Button
            type='submit'
            id='save-org-btn'
            data-test='save-org-btn'
            disabled={isSaving || !name}
            className='ml-3'
          >
            {isSaving ? 'Updating' : 'Update'}
          </Button>
        </div>
      </form>
    </FormGroup>
  )
}
