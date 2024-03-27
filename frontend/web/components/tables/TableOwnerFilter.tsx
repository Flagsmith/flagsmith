import React, { FC, useEffect, useMemo, useRef, useState } from 'react'
import { User } from 'common/types/responses'
import { AsyncStorage } from 'polyfill-react-native'
import { IonIcon } from '@ionic/react'
import { close } from 'ionicons/icons'
import SettingsButton from 'components/SettingsButton'
import UserSelect from 'components/UserSelect'
import OrganisationStore from 'common/stores/organisation-store'
import TableFilter from './TableFilter'
import TableFilterOptions from './TableFilterOptions'
import { sortBy } from 'lodash'

type TableFilterType = {
  value: number[]
  onChange: (value: TableFilterType['value']) => void
  className?: string
  useLocalStorage?: boolean
  isLoading?: boolean
  projectId: string
}

const TableOwnerFilter: FC<TableFilterType> = ({
  className,
  isLoading,
  onChange,
  projectId,
  useLocalStorage,
  value,
}) => {
  const checkedLocalStorage = useRef(false)
  const orgUsers = OrganisationStore.model && OrganisationStore.model.users
  const users = useMemo(() => {
    return sortBy(
      (orgUsers || []).map((item: User) => ({
        label: `${item.first_name} ${item.last_name}`,
        subtitle: item.email,
        value: item.id,
      })),
      'label',
    )
  }, [orgUsers, value])

  useEffect(() => {
    if (checkedLocalStorage.current && useLocalStorage) {
      AsyncStorage.setItem(`${projectId}-owners`, JSON.stringify(value))
    }
  }, [value, projectId, useLocalStorage])
  useEffect(() => {
    const checkLocalStorage = async function () {
      if (useLocalStorage && !checkedLocalStorage.current) {
        checkedLocalStorage.current = true
        const storedValue = await AsyncStorage.getItem(`${projectId}-owners`)
        if (storedValue) {
          try {
            const storedValueObject = JSON.parse(storedValue)
            onChange(storedValueObject)
          } catch (e) {}
        }
      }
    }
    checkLocalStorage()
  }, [useLocalStorage, projectId])

  return (
    <TableFilterOptions
      size='lg'
      className={className}
      isLoading={isLoading}
      title={
        <Row>
          Users{' '}
          {!!value?.length && (
            <span className='mx-1 unread d-inline'>{value.length}</span>
          )}
        </Row>
      }
      multiple
      showSearch
      options={users}
      onChange={onChange as any}
      value={value}
    />
  )
}

export default TableOwnerFilter
