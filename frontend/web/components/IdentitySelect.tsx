import React, { FC, useMemo } from 'react'
import { Identity, Res } from 'common/types/responses' // we need this to make JSX compile
import { filter, find } from 'lodash'
import { useGetIdentitiesQuery } from 'common/services/useIdentity'
import useInfiniteScroll from 'common/useInfiniteScroll'
import { Req } from 'common/types/requests'
import { components } from 'react-select'
import Utils from 'common/utils/utils'
import Button from './base/forms/Button'

export type IdentitySelectType = {
  value: { value: string; label: string } | null | undefined
  ignoreIds?: Identity['id'][]
  isEdge: boolean
  onChange: (v: { value: string; label: string }) => void
  environmentId: string
  placeholder?: string
}

const IdentitySelect: FC<IdentitySelectType> = ({
  environmentId,
  ignoreIds,
  isEdge,
  onChange,
  placeholder = 'Search Identities...',
  value,
}) => {
  const { data, isLoading, loadMore, searchItems } = useInfiniteScroll<
    Req['getIdentities'],
    Res['identities']
  >(useGetIdentitiesQuery, {
    environmentId,
    isEdge,
    page_size: 10,
  })
  const identityOptions = useMemo(() => {
    return filter(
      data?.results,
      (identity) =>
        !ignoreIds?.length ||
        !find(ignoreIds, (v) => `${v}` === `${identity.id}`),
    )
      .map(({ id: value, identifier: label }) => ({ label, value }))
      .slice(0, 10)
  }, [ignoreIds, data])
  return (
    <Flex className='text-left'>
      <Select
        onInputChange={(e: InputEvent) => {
          searchItems(Utils.safeParseEventValue(e))
        }}
        data-test='select-identity'
        placeholder={placeholder}
        value={value}
        components={{
          Menu: ({ ...props }: any) => {
            return (
              <components.Menu {...props}>
                <React.Fragment>
                  {props.children}
                  {!!data?.next && (
                    <div className='text-center mb-4'>
                      <Button
                        theme='outline'
                        onClick={() => {
                          loadMore()
                        }}
                        disabled={isLoading}
                      >
                        Load More
                      </Button>
                    </div>
                  )}
                </React.Fragment>
              </components.Menu>
            )
          },
        }}
        onChange={onChange}
        options={identityOptions}
        styles={{
          control: (base: any) => ({
            ...base,
          }),
        }}
      />
    </Flex>
  )
}

export default IdentitySelect
