import { useEffect, useRef, useState } from 'react'
import useDebounce from './useDebounce'

export default function useDebouncedSearch(
  defaultValue?: string,
  cb?: () => void,
) {
  const firstRender = useRef(true)
  const [search, setSearch] = useState(defaultValue || '')
  const [searchInput, setSearchInput] = useState(search)
  const searchItems = useDebounce((search: string) => {
    setSearch(search)
    cb?.()
  }, 500)
  useEffect(() => {
    if (firstRender.current && !searchInput) {
      firstRender.current = false
      return
    }
    firstRender.current = false
    searchItems(searchInput)
    //eslint-disable-next-line
    }, [searchInput]);
  return { search, searchInput, setSearchInput }
}
/* Usage example:
const searchItems = useDebounce((search:string) => {
  doThing()
}, 500)
*/
