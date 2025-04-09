import React, { useState, useEffect, useRef, FC } from 'react'
import Button from 'components/base/forms/Button'
import ConfigProvider from 'common/providers/ConfigProvider'
import Constants from 'common/constants'
import Icon from 'components/Icon'
import { add } from 'ionicons/icons'
import { IonIcon } from '@ionic/react'
import { getPlanBasedOption } from 'components/PlanBasedAccess'
import InputGroup from 'components/base/forms/InputGroup'
import OrganisationProvider from 'common/providers/OrganisationProvider'
import Utils from 'common/utils/utils'
import _ from 'lodash'
import ErrorMessage from 'components/ErrorMessage'
import AccountStore from 'common/stores/account-store'
import { close as closeIcon } from 'ionicons/icons'
import { MultiValueProps } from 'react-select/lib/components/MultiValue'
import { useGetGroupsQuery } from 'common/services/useGroup'
import { useCreateUserInviteMutation } from 'common/services/useInvites'
import { Req } from 'common/types/requests'

interface Invite {
  temporaryId: string
  emailAddress: string
  role?: {
    isDisabled: boolean
    label: React.ReactNode
    value: string
  }
  groups?: number[]
}

const CustomMultiValue = (props: MultiValueProps<GroupOption>) => {
  const { data, removeProps } = props

  if (!data?.label || !data?.value) {
    return null
  }

  return (
    <Row className='chip p-1'>
      <span className='font-weight-bold'>{data.label}</span>
      {
        <span className='chip-icon ion'>
          <IonIcon
            icon={closeIcon}
            onClick={() => removeProps?.onClick?.(data)}
          />
        </span>
      }
    </Row>
  )
}

type GroupOption = { label: string; value: number }

const InviteUsers: FC = () => {
  const [createUserInvite, { isLoading }] = useCreateUserInviteMutation()

  const [invites, setInvites] = useState<Invite[]>([
    { emailAddress: '', temporaryId: Utils.GUID() },
  ])
  const inputRef = useRef<HTMLInputElement>(null)

  const { id: orgId } = AccountStore.getOrganisation()

  const { data: groupData } = useGetGroupsQuery({ orgId: orgId, page: 1 })

  const groupOptions = groupData?.results.map((group) => ({
    label: group.name,
    value: group.id,
  }))

  useEffect(() => {
    const focusTimeout = setTimeout(() => {
      inputRef.current?.focus()
    }, 500)

    return () => {
      clearTimeout(focusTimeout)
    }
  }, [])

  const isValid = (): boolean => {
    return _.every(
      invites,
      (invite) => Utils.isValidEmail(invite.emailAddress) && invite.role,
    )
  }

  const onChange = (
    id: string,
    key: keyof Invite,
    value: string | number[],
  ): void => {
    setInvites((prev) =>
      prev.map((invite) => {
        if (invite.temporaryId === id) {
          return {
            ...invite,
            [key]: value,
          }
        }
        return invite
      }),
    )
  }

  const deleteInvite = (id: string): void => {
    setInvites(invites.filter((invite) => invite.temporaryId !== id))
  }

  const getPayload = (
    invites: Omit<Invite, 'temporaryId'>[],
    orgId: number,
  ): Req['createUserInvite'] => {
    return {
      invites: invites.map((invite) => ({
        email: invite.emailAddress,
        permission_groups: invite.groups ?? [],
        role: invite.role?.value ?? '',
      })),
      organisationId: orgId,
    }
  }

  return (
    <OrganisationProvider>
      {({ error, isSaving }: { error: string | null; isSaving: boolean }) => (
        <div>
          <form
            onSubmit={(e) => {
              e.preventDefault()
              createUserInvite(getPayload(invites, orgId))
                .then(() => {
                  toast('Invite sent successfully')
                })
                .catch((error) => {
                  toast('Error sending invite', 'error')
                  console.error(error)
                })
            }}
          >
            <div
              className='modal-body px-4 pt-4'
              style={{ overflowY: 'unset' }}
            >
              <Row>
                <Flex>
                  <label>Email</label>
                </Flex>
                <Flex>
                  <label className='ml-3'>Built-in role</label>
                </Flex>
                <Flex>
                  <label className='ml-3'>Groups</label>
                </Flex>
              </Row>
              {invites.map((invite, index) => (
                <Row
                  className='mb-2 align-items-start '
                  key={invite.temporaryId}
                >
                  <Flex>
                    <InputGroup
                      className='mb-2'
                      inputProps={{
                        className: 'full-width',
                        name: 'inviteEmail',
                        ref: index === 0 ? inputRef : undefined,
                      }}
                      onChange={(e) =>
                        onChange(
                          invite.temporaryId,
                          'emailAddress',
                          Utils.safeParseEventValue(e),
                        )
                      }
                      value={invite.emailAddress}
                      isValid={isValid}
                      type='text'
                      placeholder='Email'
                    />
                  </Flex>
                  <Flex className='mb-2'>
                    <Select
                      data-test='select-role'
                      placeholder='Select a role'
                      value={invite.role}
                      onChange={(role) =>
                        onChange(invite.temporaryId, 'role', role)
                      }
                      className='pl-2 react-select'
                      options={_.map(Constants.roles, (label, value) =>
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
                    />
                  </Flex>
                  <Flex className='mb-2' style={{ position: 'relative' }}>
                    <Select
                      data-test='select-group'
                      placeholder='Select a group'
                      value={invite?.groups?.map((inviteGroup) => {
                        return groupOptions?.find(
                          (g) => g.value === inviteGroup,
                        )
                      })}
                      options={groupOptions}
                      className='pl-2 react-select'
                      isMulti={true}
                      cropWithEllipsis={true}
                      components={{
                        ClearIndicator: () => null,
                        MultiValue: CustomMultiValue,
                        MultiValueContainer: () => null,
                      }}
                      onChange={(options: GroupOption[]) =>
                        onChange(
                          invite.temporaryId,
                          'groups',
                          options.map((o) => o.value),
                        )
                      }
                      styles={{
                        control: (base: any) => ({
                          ...base,
                          height: 'auto !important',
                          minHeight: '44px',
                        }),
                        multiValue: (base: any) => ({
                          ...base,
                        }),
                        valueContainer: (base: any) => ({
                          ...base,
                          gap: '4px',
                          lineHeight: '22px',
                          paddingBottom: '6px !important',
                          paddingTop: '6px  !important',
                        }),
                      }}
                    />
                  </Flex>
                  {invites.length > 1 ? (
                    <div className='ml-2'>
                      <Button
                        id='delete-invite'
                        type='button'
                        onClick={() => deleteInvite(invite.temporaryId)}
                        className='btn btn-with-icon mb-2'
                      >
                        <Icon name='trash-2' width={20} fill='#656D7B' />
                      </Button>
                    </div>
                  ) : (
                    <div />
                  )}
                </Row>
              ))}

              <div className='text-right mt-4'>
                <Button
                  theme='outline'
                  size='small'
                  id='btn-add-invite'
                  disabled={isSaving || isLoading || !isValid()}
                  type='button'
                  onClick={() =>
                    setInvites([
                      ...invites,
                      { emailAddress: '', temporaryId: Utils.GUID() },
                    ])
                  }
                >
                  <Row>
                    <span className='pl-2 icon'>
                      <IonIcon icon={add} style={{ fontSize: '13px' }} />
                    </span>
                    <span>
                      {isSaving ? 'Sending' : 'Invite additional member'}
                    </span>
                  </Row>
                </Button>
              </div>

              <div className='mt-5'>
                Users without administrator privileges will need to be invited
                to individual projects.
                <div>
                  <Button
                    theme='text'
                    target='_blank'
                    href='https://docs.flagsmith.com/system-administration/rbac'
                    className='fw-normal'
                  >
                    Learn about User Roles.
                  </Button>
                </div>
              </div>
              {error && <ErrorMessage error={error} />}
            </div>
            <div className='modal-footer pt-5'>
              <Button
                id='btn-send-invite'
                disabled={isSaving || !isValid()}
                onClick={() => closeModal()}
                type='submit'
              >
                {isSaving ? 'Sending' : 'Send Invitation'}
              </Button>
            </div>
          </form>
        </div>
      )}
    </OrganisationProvider>
  )
}

export default ConfigProvider(InviteUsers)
