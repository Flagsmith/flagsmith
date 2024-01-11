import { FC, useCallback } from 'react'

import AccountProvider from 'common/providers/AccountProvider'
import AccountStore from 'common/stores/account-store'
import AppActions from 'common/dispatcher/app-actions'
import Utils from 'common/utils/utils'
import Project from 'common/project'
import Button from 'components/base/forms/Button'
import CreateOrganisationModal from 'components/modals/CreateOrganisation'
import Icon from './Icon'
import OrganisationSelect from './OrganisationSelect'

interface OrganisationManageWidgetType {
  disableCreate?: boolean
}

const OrganisationManageWidget: FC<OrganisationManageWidgetType> = ({
  disableCreate,
}) => {
  const handleCreateOrganisationClick = useCallback(() => {
    openModal('Create Organisation', <CreateOrganisationModal />, 'side-modal')
  }, [])

  return (
    <Row>
      <AccountProvider>
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
      {!disableCreate &&
        !Utils.getFlagsmithHasFeature('disable_create_org') &&
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
