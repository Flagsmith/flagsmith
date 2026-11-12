import { FC, useId, useState } from 'react'
import Button from 'components/base/forms/Button'
import Chip from 'components/base/Chip'
import FieldLabel from 'components/base/forms/FieldLabel'
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
  const isAdminId = useId()
  const rolesLabelId = useId()

  return (
    <>
      <Row className='mb-3 mt-4 gap-2'>
        <FieldLabel htmlFor={isAdminId} className='mb-0'>
          Is admin
        </FieldLabel>
        <Switch
          id={isAdminId}
          onChange={onIsAdminChange}
          checked={isAdmin}
          disabled={!Utils.getPlansPermission('RBAC') && isAdmin}
        />
        <PlanBasedBanner feature='RBAC' theme='badge' />
      </Row>
      <PlanBasedBanner feature='RBAC' theme='description' className='mb-4' />
      {!isAdmin && (
        <>
          <Row className='mb-3 gap-2'>
            <FieldLabel id={rolesLabelId} className='mb-0'>
              Roles
            </FieldLabel>
            <div
              role='group'
              aria-labelledby={rolesLabelId}
              className='d-flex flex-wrap gap-2'
            >
              {roles.map((role) => (
                <Chip
                  key={role.id}
                  variant='accent'
                  onRemove={() => onRemoveRole(role.id)}
                >
                  {role.name}
                </Chip>
              ))}
            </div>
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
