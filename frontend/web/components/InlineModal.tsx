import React, { useRef, FC, useEffect } from 'react'
import ModalClose from './modals/base/ModalClose'
import ModalHR from './modals/ModalHR'
import Icon from './Icon'
import classNames from 'classnames'
import useOutsideClick from 'common/useOutsideClick'

interface InlineModalProps {
  bottom?: React.ReactNode
  children?: React.ReactNode
  className?: string
  containerClassName?: string
  hideClose?: boolean
  isOpen?: boolean
  onBack?: () => void
  onClose: () => void
  relativeToParent?: boolean
  showBack?: boolean
  title?: string | React.ReactNode
}

const InlineModal: FC<InlineModalProps> = ({
  bottom,
  children,
  className,
  containerClassName,
  hideClose = false,
  isOpen = false,
  onBack,
  onClose,
  relativeToParent = false,
  showBack = false,
  title,
}) => {
  const modalRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (isOpen) {
      document.body.classList.add('inline-modal-open')
    } else {
      document.body.classList.remove('inline-modal-open')
    }
    return () => {
      document.body.classList.remove('inline-modal-open')
    }
  }, [isOpen])
  useOutsideClick(modalRef, () => {
    if (isOpen) {
      onClose()
    }
  })

  return (
    <div className={relativeToParent ? '' : 'relative'}>
      {isOpen && (
        <div ref={modalRef} className={classNames('inline-modal', className)}>
          <div className='d-flex py-2 d-lg-none justify-content-end px-4'>
            <ModalClose onClick={onClose} />
          </div>
          {(!!title || !hideClose) && (
            <>
              <div className='inline-modal__title'>
                <Row className='no-wrap' space>
                  <Row className='flex-fill'>
                    {showBack && (
                      <span
                        onClick={onBack}
                        className='modal-back-btn clickable'
                      >
                        <Icon name='arrow-left' fill='#9DA4AE' />
                      </span>
                    )}
                    {typeof title === 'string' ? (
                      <h5 className='mb-0'>{title}</h5>
                    ) : (
                      title
                    )}
                  </Row>
                  {!hideClose && <ModalClose onClick={onClose} />}
                </Row>
              </div>
              <ModalHR />
            </>
          )}

          <div
            className={classNames(
              'inline-modal__content',
              containerClassName || 'p-3',
            )}
          >
            {children}
          </div>
          {bottom && (
            <>
              <ModalHR />
              <div className='inline-modal__bottom p-3'>{bottom}</div>
            </>
          )}
        </div>
      )}
    </div>
  )
}

InlineModal.displayName = 'Popover'

export default InlineModal
