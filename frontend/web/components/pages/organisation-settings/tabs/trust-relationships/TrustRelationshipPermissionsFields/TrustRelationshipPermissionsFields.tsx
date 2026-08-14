import React, { FC, useState } from 'react'
import { IonIcon } from '@ionic/react'
import { close as closeIcon } from 'ionicons/icons'
import Button from 'components/base/forms/Button'
import PlanBasedBanner from 'components/PlanBasedAccess'
import Switch from 'components/Switch'
import MyRoleSelect from 'components/MyRoleSelect'
import Utils from 'common/utils/utils'

export type SelectedRole = { id: number; name: string }

type TrustRelationshipPermissionsFieldsProps = {
  organisationId: number
  isAdmin: boolean
  onIsAdminChange: () => void
  roles: SelectedRole[]
  onAddRole: (role: SelectedRole) => void
  onRemoveRole: (roleId: number) => void
}

const TrustRelationshipPermissionsFields: FC<
  TrustRelationshipPermissionsFieldsProps
> = ({
  isAdmin,
  onAddRole,
  onIsAdminChange,
  onRemoveRole,
  organisationId,
  roles,
}) => {
  const [showRoles, setShowRoles] = useState(false)

  return (
    <>
      <Row className='mb-3 mt-4 gap-2'>
        <label className='mb-0'>Is admin</label>
        <Switch
          onChange={onIsAdminChange}
          checked={isAdmin}
          disabled={!Utils.getPlansPermission('RBAC') && isAdmin}
        />
        <PlanBasedBanner feature='RBAC' theme='badge' />
      </Row>
      <PlanBasedBanner feature='RBAC' theme='description' className='mb-4' />
      {!isAdmin && (
        <>
          <Row className='mb-3'>
            <label className='mr-2'>Roles:</label>
            {roles.map((role) => (
              <Row
                key={role.id}
                role='button'
                tabIndex={0}
                aria-label={`Remove role ${role.name}`}
                onClick={() => onRemoveRole(role.id)}
                onKeyDown={(e: React.KeyboardEvent) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault()
                    onRemoveRole(role.id)
                  }
                }}
                className='chip'
              >
                <span className='font-weight-bold'>{role.name}</span>
                <span className='chip-icon ion'>
                  <IonIcon icon={closeIcon} style={{ fontSize: '13px' }} />
                </span>
              </Row>
            ))}
          </Row>
          <Row className='mb-3'>
            <Button theme='text' onClick={() => setShowRoles(!showRoles)}>
              Select roles
            </Button>
            <div className='px-4'>
              <MyRoleSelect
                isRoleApiKey
                orgId={organisationId}
                value={roles.map((role) => role.id)}
                onAdd={(role) => onAddRole(role as unknown as SelectedRole)}
                onRemove={onRemoveRole}
                isOpen={showRoles}
                onToggle={() => setShowRoles(!showRoles)}
              />
            </div>
          </Row>
        </>
      )}
    </>
  )
}

export default TrustRelationshipPermissionsFields
