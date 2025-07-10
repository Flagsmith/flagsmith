import React from 'react'
import { Organisation, User } from 'common/types/responses'
import classNames from 'classnames'
import Constants from 'common/constants'
import AccountStore from 'common/stores/account-store'
import map from 'lodash/map'
import Utils from 'common/utils/utils'
import UserAction from 'components/UserAction'
import LastLogin from './LastLogin'
import AppActions from 'common/dispatcher/app-actions'
import { getPlanBasedOption } from 'components/PlanBasedAccess'

interface OrganisationUsersTableRowProps {
  widths: number[]
  inspectPermissions: (user: User, organisationId: number) => void
  onEditClick: () => void
  onRemoveClick: () => void
  user: User
  organisation: Organisation
}

const OrganisationUsersTableRow: React.FC<OrganisationUsersTableRowProps> = ({
  inspectPermissions,
  onEditClick,
  onRemoveClick,
  organisation,
  user,
  widths,
}) => {
  const { email, first_name, id, last_login, last_name, role } = user
  const isActiveUser = id === AccountStore.getUserId()
  const roleChanged = (id: number, { value: role }: { value: string }) => {
    AppActions.updateUserRole(id, role)
  }
  const isInspectPermissionsEnabled = Utils.getFlagsmithHasFeature(
    'inspect_permissions',
  )
  return (
    <Row
      data-test={`user-${email}`}
      space
      className={classNames('list-item clickable')}
      onClick={onEditClick}
      key={id}
    >
      <Flex className='table-column px-3 font-weight-medium'>
        {`${first_name} ${last_name}`} {isActiveUser && '(You)'}
        <div className='list-item-subtitle mt-1'>{email}</div>
      </Flex>

      <div
        style={{
          width: widths[0],
        }}
        className='table-column'
      >
        <div>
          {organisation.role === 'ADMIN' && !isActiveUser ? (
            <div>
              <Select
                data-test='select-role'
                placeholder='Select a role'
                value={
                  role && {
                    label: Constants.roles[role],
                    value: role,
                  }
                }
                onChange={(e: InputEvent) =>
                  roleChanged(id, Utils.safeParseEventValue(e))
                }
                options={map(Constants.roles, (label, value) =>
                  value === 'ADMIN'
                    ? {
                        label,
                        value,
                      }
                    : getPlanBasedOption(
                        {
                          label,
                          value,
                        },
                        'RBAC',
                      ),
                )}
                menuPortalTarget={document.body}
                menuPosition='absolute'
                menuPlacement='auto'
                className='react-select select-xsm'
              />
            </div>
          ) : (
            <div className='px-3 fs-small lh-sm'>
              {Constants.roles[role] || ''}
            </div>
          )}
        </div>
      </div>
      <div
        style={{
          width: widths[1],
        }}
        className='table-column'
      >
        <LastLogin lastLogin={last_login} />
      </div>
      <div
        style={{
          width: widths[2],
        }}
        className='table-column d-flex justify-content-end'
      >
        <UserAction
          onRemove={onRemoveClick}
          onEdit={onEditClick}
          canRemove={AccountStore.isAdmin()}
          canEdit={AccountStore.isAdmin()}
          canInspectPermissions={
            isInspectPermissionsEnabled && AccountStore.isAdmin()
          }
          onInspectPermissions={() => {
            inspectPermissions(user, organisation.id)
          }}
        />
      </div>
    </Row>
  )
}

export default OrganisationUsersTableRow
