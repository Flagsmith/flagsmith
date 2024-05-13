import React, { Component } from 'react'
import InfoMessage from 'components/InfoMessage'
import ErrorMessage from 'components/ErrorMessage'
import Button from 'components/base/forms/Button'
import Constants from 'common/constants'
import { setInterceptClose } from './base/ModalDefault'

const CreateProject = class extends Component {
  static displayName = 'CreateProject'

  constructor(props, context) {
    super(props, context)
    this.state = {}
  }

  close = (data = {}) => {
    setInterceptClose(null)
    closeModal()
    if (data) {
      const { environmentId, projectId } = data
      this.props.history.push(
        `/project/${projectId}/environment/${environmentId}/features?new=true`,
      )
      this.props.onSave?.(data)
    }
  }

  componentDidMount = () => {
    this.focusTimeout = setTimeout(() => {
      this.input.focus()
      this.focusTimeout = null
    }, 500)

    setInterceptClose(() => {
      return new Promise((resolve) => {
        this.props.history.push(document.location.pathname)
        setInterceptClose(null)
        resolve(true)
      })
    })
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
            <div className='p-4'>
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
                {disableCreate && (
                  <InfoMessage>
                    View and manage multiple projects in your organisation with
                    the{' '}
                    <a
                      href='#'
                      onClick={() => {
                        document.location.replace(Constants.upgradeURL)
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
                <div className='text-right mt-5'>
                  <Button
                    type='submit'
                    data-test='create-project-btn'
                    id='create-project-btn'
                    disabled={isSaving || !name}
                    className='text-right'
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

export default CreateProject
