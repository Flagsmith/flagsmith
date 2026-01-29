import { FC, useState } from 'react'
import { useHistory, useLocation, Link } from 'react-router-dom'
import SuccessMessage from 'components/messages/SuccessMessage'
import Utils from 'common/utils/utils'

type ImportSuccessBannerProps = {
  projectId: string
  environmentId: string
}

const ImportSuccessBanner: FC<ImportSuccessBannerProps> = ({
  environmentId,
  projectId,
}) => {
  const history = useHistory()
  const location = useLocation()
  const [dismissed, setDismissed] = useState(false)

  const params = Utils.fromParam()
  const isImportSuccess = params.import_success === '1'
  const source = params.import_source
  const count = parseInt(params.import_count, 10)
  const deprecated = parseInt(params.import_deprecated, 10) || 0

  if (!isImportSuccess || !source || !count || dismissed) {
    return null
  }

  const handleDismiss = () => {
    setDismissed(true)
    history.replace(location.pathname)
  }

  const archivedLink = `/project/${projectId}/environment/${environmentId}/features?is_archived=true`

  return (
    <div className='mb-4'>
      <SuccessMessage isClosable close={handleDismiss}>
        Imported {count} flag{count !== 1 && 's'} from {source}.
        {deprecated > 0 && (
          <>
            {' '}
            {deprecated} deprecated flag
            {deprecated !== 1 ? 's were' : ' was'}{' '}
            <Link to={archivedLink}>archived</Link>.
          </>
        )}
      </SuccessMessage>
    </div>
  )
}

export default ImportSuccessBanner
