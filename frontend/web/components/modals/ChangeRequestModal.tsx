import React, { useState, useEffect, FC, useMemo } from 'react'
import UserSelect from 'components/UserSelect'
import OrganisationProvider from 'common/providers/OrganisationProvider'
import Button from 'components/base/forms/Button'
import MyGroupsSelect from 'components/MyGroupsSelect'
import { useGetMyGroupsQuery } from 'common/services/useMyGroup'
import DateSelect, { DateSelectProps } from 'components/DateSelect'
import { close } from 'ionicons/icons'
import { IonIcon } from '@ionic/react'
import InfoMessage from 'components/InfoMessage'
import AccountStore from 'common/stores/account-store'
import InputGroup from 'components/base/forms/InputGroup'
import moment from 'moment'
import Utils from 'common/utils/utils'
import { Approval, ChangeRequest, User } from 'common/types/responses'
import { Req } from 'common/types/requests'

interface ChangeRequestModalProps {
  changeRequest?: ChangeRequest
  onSave: (
    data: Omit<Req['createChangeRequest'], 'multivariate_options'>,
  ) => void
  isScheduledChange?: boolean
  showAssignees?: boolean
}

const ChangeRequestModal: FC<ChangeRequestModalProps> = ({
  changeRequest,
  isScheduledChange,
  onSave,
  showAssignees,
}) => {
  const [approvals, setApprovals] = useState<Approval[]>([
    ...(changeRequest?.approvals ?? []),
    ...(changeRequest?.group_assignments ?? []),
  ])
  const [description, setDescription] = useState<string>(
    String(changeRequest?.description ?? ''),
  )
  // const [groups, setGroups] = useState([])
  const [liveFrom, setLiveFrom] = useState(
    changeRequest?.feature_states[0]?.live_from,
  )
  const [title, setTitle] = useState(changeRequest?.title ?? '')
  const [showUsers, setShowUsers] = useState(false)
  const [showGroups, setShowGroups] = useState(false)
  const [currDate, setCurrDate] = useState(new Date())

  const { data: groups } = useGetMyGroupsQuery({
    orgId: AccountStore.getOrganisation().id,
  })

  useEffect(() => {
    const currLiveFromDate = changeRequest?.feature_states[0]?.live_from
    if (!currLiveFromDate) {
      return setLiveFrom(showAssignees ? currDate.toISOString() : undefined)
    }
  }, [isScheduledChange, showAssignees, changeRequest, currDate])

  const addOwner = (id: number, isUser = true) => {
    if (!isUser) {
      setApprovals((prev) => [...prev, { group: id }])
      return
    }

    setApprovals((prev) => [...prev, { user: id }])
  }

  const removeOwner = (id: number, isUser = true) => {
    if (!isUser) {
      setApprovals((prev) => prev.filter((v) => v.group !== id))
      return
    }

    setApprovals((prev) => prev.filter((v) => v.user !== id))
  }

  const getApprovals = (users: User[], approvals: Approval[]) =>
    users.filter((u) => approvals.find((a) => a.user === u.id))

  const ownerGroups = useMemo(
    () =>
      groups?.results?.filter((g) => approvals.find((a) => a.group === g.id)),
    [groups?.results, approvals],
  )

  const save = () => {
    onSave({
      approvals,
      description,
      live_from: liveFrom || undefined,
      title,
    })
  }

  const handleClear = () => {
    const newCurrDate = new Date()
    setCurrDate(newCurrDate)
    setLiveFrom(showAssignees ? newCurrDate.toISOString() : undefined)
  }

  const handleOnDateChange: DateSelectProps['onChange'] = (date) => {
    setLiveFrom(date?.toISOString())
  }

  const isValid = useMemo(() => {
    return !!title?.length && !!liveFrom
  }, [title, liveFrom])

  return (
    <OrganisationProvider>
      {({ users }) => {
        const ownerUsers = getApprovals(users, approvals)
        return (
          <div>
            <FormGroup className='mb-4'>
              <InputGroup
                value={title}
                onChange={(e: Event) => setTitle(Utils.safeParseEventValue(e))}
                isValid={!!title && title.length > 0}
                type='text'
                title='Title'
                inputProps={{ className: 'full-width' }}
                className='full-width'
                placeholder='My Change Request'
              />
            </FormGroup>
            <FormGroup className='mb-4'>
              <InputGroup
                textarea
                value={description}
                onChange={(e: Event) =>
                  setDescription(Utils.safeParseEventValue(e))
                }
                type='text'
                title='Description'
                inputProps={{
                  className: 'full-width',
                  style: { minHeight: 80 },
                }}
                className='full-width'
                placeholder='Add an optional description...'
              />
            </FormGroup>
            <div>
              <InputGroup
                tooltip='Allows you to set a date and time in which your change will only become active. All dates are displayed in your local timezone.'
                title='Schedule Change'
                component={
                  <Row>
                    <DateSelect
                      isValid={!!liveFrom?.length}
                      dateFormat='MMMM d, yyyy h:mm aa'
                      onChange={handleOnDateChange}
                      selected={liveFrom ? moment(liveFrom).toDate() : null}
                    />
                    <Button
                      className='ml-2'
                      onClick={handleClear}
                      theme='secondary'
                      size='large'
                    >
                      Clear
                    </Button>
                  </Row>
                }
              />
            </div>
            {showAssignees && moment(liveFrom).isSame(currDate) && (
              <InfoMessage>
                <strong>
                  Changes will take effect immediately after approval.
                </strong>
              </InfoMessage>
            )}
            {liveFrom && moment(liveFrom).isAfter(moment()) && (
              <InfoMessage>
                This change will be scheduled to go live at{' '}
                <strong>
                  {moment(liveFrom).format('Do MMM YYYY hh:mma')} (
                  {Intl.DateTimeFormat().resolvedOptions().timeZone} Time).
                </strong>
              </InfoMessage>
            )}
            {!changeRequest &&
              showAssignees &&
              !Utils.getFlagsmithHasFeature('disable_users_as_reviewers') && (
                <FormGroup className='mb-4'>
                  <InputGroup
                    component={
                      <div>
                        {!Utils.getFlagsmithHasFeature(
                          'disable_users_as_reviewers',
                        ) && (
                          <Row>
                            <strong style={{ width: 70 }}> Users: </strong>
                            {ownerUsers.map((u) => (
                              <Row
                                key={u.id}
                                onClick={() => removeOwner(u.id)}
                                className='chip'
                                style={{ marginBottom: 4, marginTop: 4 }}
                              >
                                <span className='font-weight-bold'>
                                  {u.first_name} {u.last_name}
                                </span>
                                <span className='chip-icon ion'>
                                  <IonIcon icon={close} />
                                </span>
                              </Row>
                            ))}
                            <Button
                              theme='text'
                              onClick={() => setShowUsers(true)}
                            >
                              Add user
                            </Button>
                          </Row>
                        )}
                        <Row>
                          <strong style={{ width: 70 }}> Groups: </strong>
                          {ownerGroups?.map((u) => (
                            <Row
                              key={u.id}
                              onClick={() => removeOwner(u.id, false)}
                              className='chip'
                              style={{ marginBottom: 4, marginTop: 4 }}
                            >
                              <span className='font-weight-bold'>{u.name}</span>
                              <span className='chip-icon ion'>
                                <IonIcon icon={close} />
                              </span>
                            </Row>
                          ))}
                          <Button
                            theme='text'
                            onClick={() => setShowGroups(true)}
                          >
                            Add group
                          </Button>
                        </Row>
                      </div>
                    }
                    onChange={(e: Event) =>
                      setDescription(Utils.safeParseEventValue(e))
                    }
                    type='text'
                    title='Assignees'
                    tooltipPlace='top'
                    tooltip='Assignees will be able to review and approve the change request'
                    inputProps={{
                      className: 'full-width',
                      style: { minHeight: 80 },
                    }}
                    className='full-width'
                    placeholder='Add an optional description...'
                  />
                </FormGroup>
              )}
            {!changeRequest &&
              !Utils.getFlagsmithHasFeature('disable_users_as_reviewers') && (
                <UserSelect
                  users={users.filter(
                    (v) => v.id !== AccountStore.getUser().id,
                  )}
                  value={approvals.map((v) => v.user)}
                  onAdd={addOwner}
                  onRemove={removeOwner}
                  isOpen={showUsers}
                  onToggle={() => setShowUsers(!showUsers)}
                />
              )}
            {!changeRequest && (
              <MyGroupsSelect
                orgId={AccountStore.getOrganisation().id}
                value={approvals.map((v) => Number(v.group))}
                onAdd={addOwner}
                onRemove={removeOwner}
                isOpen={showGroups}
                onToggle={() => setShowGroups(!showGroups)}
                size='-sm'
              />
            )}
            <FormGroup className='text-right mt-2'>
              <Button
                id='confirm-cancel-plan'
                className='btn btn-primary'
                disabled={!isValid}
                onClick={save}
              >
                {changeRequest ? 'Update' : 'Create'}
              </Button>
            </FormGroup>
          </div>
        )
      }}
    </OrganisationProvider>
  )
}

export default ChangeRequestModal
