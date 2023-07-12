import React, { Component } from 'react'
import InfoMessage from 'components/InfoMessage'
import PaymentModal from './Payment'
import ErrorMessage from 'components/ErrorMessage'
import Button from 'components/base/forms/Button'
import ModalHR from './ModalHR'

const CreateProject = class extends Component {
  static displayName = 'CreateProject'

  constructor(props, context) {
    super(props, context)
    this.state = {}
  }

  close = (id) => {
    closeModal()
    this.props.onSave(id)
  }

  componentDidMount = () => {
    this.focusTimeout = setTimeout(() => {
      this.input.focus()
      this.focusTimeout = null
    }, 500)
  }

  componentWillUnmount() {
    if (this.focusTimeout) {
      clearTimeout(this.focusTimeout)
    }
  }

  render() {
    const { name } = this.state
    return (
      <OrganisationProvider onSave={this.close}>
        {({ createProject, error, isSaving, projects }) => {
          const hasProject = !!projects && !!projects.length
          const canCreate = !!Utils.getPlansPermission(
            'CREATE_ADDITIONAL_PROJECT',
          )
          const disableCreate = !canCreate && hasProject

          return (
            <div>
              <form
                style={{ opacity: disableCreate ? 0.5 : 1 }}
                data-test='create-project-modal'
                id='create-project-modal'
                onSubmit={(e) => {
                  if (disableCreate) {
                    return
                  }
                  e.preventDefault()
                  !isSaving && name && createProject(name)
                }}
              >
                <div className='modal-body'>
                  {disableCreate && (
                    <InfoMessage>
                      View and manage multiple projects in your organisation
                      with the{' '}
                      <a
                        href='#'
                        onClick={() => {
                          openModal(
                            'Payment plans',
                            <PaymentModal viewOnly={false} />,
                            'modal-lg',
                          )
                        }}
                      >
                        Startup plan
                      </a>
                    </InfoMessage>
                  )}
                  <InputGroup
                    ref={(e) => (this.input = e)}
                    data-test='projectName'
                    disabled={disableCreate}
                    className='mb-0'
                    inputProps={{
                      className: 'full-width',
                      name: 'projectName',
                    }}
                    onChange={(e) =>
                      this.setState({ name: Utils.safeParseEventValue(e) })
                    }
                    isValid={name && name.length}
                    type='text'
                    title='Project Name*'
                    placeholder='My Product Name'
                  />
                  {error && <ErrorMessage error={error} />}
                </div>
                <ModalHR />
                <div className='modal-footer'>
                  <Button
                    onClick={closeModal}
                    theme='secondary'
                    className='mr-2'
                  >
                    Cancel
                  </Button>
                  <Button
                    type='submit'
                    data-test='create-project-btn'
                    id='create-project-btn'
                    disabled={isSaving || !name}
                  >
                    {isSaving ? 'Creating' : 'Create Project'}
                  </Button>
                </div>
              </form>
            </div>
          )
        }}
      </OrganisationProvider>
    )
  }
}

CreateProject.propTypes = {}

module.exports = CreateProject
