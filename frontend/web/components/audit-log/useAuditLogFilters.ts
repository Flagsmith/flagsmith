import { useEffect, useRef, useState } from 'react'
import { useHistory, useLocation } from 'react-router-dom'
import useDebounce from 'common/useDebounce'
import {
  AuditLogFilters,
  DEFAULT_AUDIT_LOG_FILTERS,
  parseAuditLogFilters,
} from './auditLogFilters'

// The URL holds the filters, so a filtered view can be shared as a link and
// the Audit Log tab, which links without them, resets them.
export default function useAuditLogFilters() {
  const history = useHistory()
  const location = useLocation()
  const filters: AuditLogFilters = parseAuditLogFilters(
    new URLSearchParams(location.search),
  )
  const [searchInput, setSearchInputState] = useState(filters.search)
  const lastWrittenSearch = useRef(filters.search)
  // Bumped to drop a search still waiting on the debounce.
  const pendingWrite = useRef(0)

  const writeSearch = (search: string, write = pendingWrite.current) => {
    if (write !== pendingWrite.current) return
    lastWrittenSearch.current = search
    // history.location, not location: this runs after the debounce.
    const params = new URLSearchParams(history.location.search)
    if (search) params.set('search', search)
    else params.delete('search')
    history.replace({ ...history.location, search: params.toString() })
  }
  const writeSearchLater = useDebounce(writeSearch, 500)

  // The URL changed from elsewhere, e.g. the Audit Log tab: show its search.
  useEffect(() => {
    if (filters.search !== lastWrittenSearch.current) {
      pendingWrite.current += 1
      lastWrittenSearch.current = filters.search
      setSearchInputState(filters.search)
    }
  }, [filters.search])

  const setSearchInput = (value: string) => {
    setSearchInputState(value)
    writeSearchLater(value, pendingWrite.current)
  }

  const clearFilters = () => {
    pendingWrite.current += 1
    setSearchInputState(DEFAULT_AUDIT_LOG_FILTERS.search)
    writeSearch(DEFAULT_AUDIT_LOG_FILTERS.search)
  }

  return { clearFilters, filters, searchInput, setSearchInput }
}
