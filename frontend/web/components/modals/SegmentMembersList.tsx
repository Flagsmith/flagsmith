import React, { FC, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import PanelSearch from 'components/PanelSearch'
import Utils from 'common/utils/utils'
import useDebouncedSearch from 'common/useDebouncedSearch'
import { useGetSegmentMembersQuery } from 'common/services/useSegmentMembers'
import type { SegmentMember } from 'common/types/responses'

const PAGE_SIZE = 10

type SegmentMembersListProps = {
  projectId: string | number
  segmentId: number
  environmentId: number
  environmentApiKey: string
  // Total members for the selected environment, from the segment's
  // membership_counts. The list endpoint is cursor-paginated and returns no
  // count, so this drives the title total rather than the pager.
  count?: number
}

// Lists the identities currently matching a segment, using the cursor-paginated
// segment members endpoint. Unlike the legacy identities list, every row here
// is a confirmed member, so no per-row membership check is needed. Cursor paging
// mirrors the edge identities list: the cursor stack lives in `pages` and the
// response carries the `next`/`previous` flags (via `transformCursorPaging`).
const SegmentMembersList: FC<SegmentMembersListProps> = ({
  count,
  environmentApiKey,
  environmentId,
  projectId,
  segmentId,
}) => {
  const { search, searchInput, setSearchInput } = useDebouncedSearch('')

  // Cursor stack of the pages stepped through; the last entry is the cursor for
  // the current page, an empty stack is the first page.
  const [pages, setPages] = useState<(string | undefined)[]>([])

  // Reset paging whenever the environment or search term changes.
  useEffect(() => {
    setPages([])
  }, [environmentId, search])

  const { data, isFetching } = useGetSegmentMembersQuery(
    {
      environment: environmentId,
      id: segmentId,
      page_size: PAGE_SIZE,
      pages,
      projectId: Number(projectId),
      q: search || undefined,
    },
    { skip: !environmentId },
  )

  return (
    <PanelSearch
      renderSearchWithNoResults
      id='segment-members-list'
      title={
        count !== undefined
          ? `Segment Users (${Utils.numberWithCommas(count)})`
          : 'Segment Users'
      }
      className='no-pad'
      isLoading={isFetching}
      items={data?.results}
      paging={data}
      nextPage={() => {
        setPages(data?.next_cursor ? pages.concat([data.next_cursor]) : pages)
      }}
      prevPage={() => {
        setPages(Utils.removeElementFromArray(pages, pages.length - 1))
      }}
      goToPage={() => {
        // Cursor pagination cannot jump to an arbitrary page.
      }}
      renderRow={({ identifier }: SegmentMember, index: number) => (
        <Link
          to={`/project/${projectId}/environment/${environmentApiKey}/identities/${encodeURIComponent(
            identifier,
          )}`}
          className='list-item list-item-sm clickable d-flex align-items-center px-3'
          data-test={`segment-member-${index}`}
        >
          <div className='font-weight-medium'>{identifier}</div>
        </Link>
      )}
      filterRow={() => true}
      search={searchInput}
      onChange={(e) => {
        setSearchInput(Utils.safeParseEventValue(e))
      }}
    />
  )
}

export default SegmentMembersList
