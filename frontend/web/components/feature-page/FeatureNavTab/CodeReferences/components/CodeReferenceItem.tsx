import flagsmith from '@flagsmith/flagsmith'
import Icon from 'components/icons/Icon'
import { CodeReference, VCSProvider } from 'common/types/responses'

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
      <a
        className='text-sm text-gray-500 mb-0'
        style={{
          fontStyle: 'italic',
          fontWeight: 400,
          textDecoration: 'underline',
        }}
        href={codeReference.permalink}
        target='_blank'
        rel='noreferrer'
        onClick={() => {
          flagsmith.trackEvent('code_references_click_permalink', {
            feature_id: featureId,
            vcs_provider: vcsProvider,
          })
        }}
      >
        {codeReference.file_path}:{codeReference.line_number}
      </a>
    </Row>
  )
}

export default CodeReferenceItem
