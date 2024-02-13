import { FC, useCallback, useEffect } from 'react'

import AccountProvider from 'common/providers/AccountProvider'
import AccountStore from 'common/stores/account-store'
import AppActions from 'common/dispatcher/app-actions'
import Utils from 'common/utils/utils'
import Project from 'common/project'
import Button from './base/forms/Button'
import CreateOrganisationModal from './modals/CreateOrganisation'
import Icon from './Icon'
import OrganisationSelect from './OrganisationSelect'

type OrganisationManageWidgetType = {
  onChange?: () => void
}

const OrganisationManageWidget: FC<OrganisationManageWidgetType> = ({
  onChange,
}) => {
  const handleCreateOrganisationClick = useCallback(() => {
    openModal('Create Organisation', <CreateOrganisationModal />, 'side-modal')
  }, [])

  useEffect(() => {
    AppActions.getOrganisation(AccountStore.getOrganisation().id)
  }, [])

  return (
    <Row>
      <AccountProvider onChange={() => onChange && onChange()}>
        {({ organisation }: { organisation: unknown }) =>
          organisation && (
            <OrganisationSelect
              onChange={(organisationId: string) => {
                AppActions.selectOrganisation(organisationId)
                AppActions.getOrganisation(organisationId)
              }}
            />
          )
        }
      </AccountProvider>
      {!Utils.getFlagsmithHasFeature('disable_create_org') &&
        (!Project.superUserCreateOnly ||
          (Project.superUserCreateOnly && AccountStore.isSuper())) && (
          <div>
            <Flex className='text-center ml-3'>
              <Button
                data-test='create-organisation-btn'
                onClick={handleCreateOrganisationClick}
                size='large'
                className='btn btn-with-icon btn-lg px-3'
              >
                <Icon name='plus' width={24} fill='#656D7B' />
              </Button>
            </Flex>
          </div>
        )}
    </Row>
  )
}

export default OrganisationManageWidget
