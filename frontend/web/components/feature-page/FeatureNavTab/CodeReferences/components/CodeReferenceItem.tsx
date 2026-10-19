import flagsmith from '@flagsmith/flagsmith'
import Icon from 'components/icons/Icon'
import { CodeReference, VCSProvider } from 'common/types/responses'
import Link from 'components/base/link'

interface CodeReferenceItemProps {
  codeReference: CodeReference
  featureId: number
  vcsProvider: VCSProvider
}

const CodeReferenceItem: React.FC<CodeReferenceItemProps> = ({
  codeReference,
  featureId,
  vcsProvider,
}) => {
  return (
    <Row className='flex items-center gap-1' noWrap>
      <Icon
        name={'chevron-down'}
        className='w-4 h-4 transparent'
        style={{ visibility: 'hidden' }}
      />
      <Link
        className='fst-italic'
        href={codeReference.permalink}
        target='_blank'
        onClick={() => {
          flagsmith.trackEvent('code_references_click_permalink', {
            metadata: {
              feature_id: featureId,
              vcs_provider: vcsProvider,
            },
          })
        }}
      >
        {codeReference.file_path}:{codeReference.line_number}
      </Link>
    </Row>
  )
}

export default CodeReferenceItem
