import React, { Component } from 'react'
import ModalHR from './ModalHR'

const ConfirmRemoveFeature = class extends Component {
  static displayName = 'ConfirmRemoveFeature'

  constructor(props, context) {
    super(props, context)
    this.state = {
      name: props.name,
    }
  }

  close() {
    closeModal()
  }

  submit = (e) => {
    const { projectFlag } = this.props
    e.preventDefault()
    if (this.state.challenge == projectFlag.name) {
      this.close()
      this.props.cb()
    }
  }

  render() {
    const { identity, projectFlag } = this.props
    return (
      <ProjectProvider>
        {() => (
          <form id='confirm-remove-feature-modal' onSubmit={this.submit}>
            <div className='modal-body'>
              <>
                {identity ? (
                  <p>
                    This will reset <strong>{projectFlag.name}</strong> for to
                    the environment defaults for the user{' '}
                    <strong>{identity}</strong>
                  </p>
                ) : (
                  <p>
                    This will remove <strong>{projectFlag.name}</strong> for{' '}
                    <strong>all environments</strong>. You should ensure that
                    you do not contain any references to this feature in your
                    applications before proceeding.
                  </p>
                )}

                <InputGroup
                  className='mb-0'
                  inputProps={{
                    className: 'full-width',
                    name: 'confirm-feature-name',
                  }}
                  title='Please type the feature name to confirm'
                  placeholder='feature_name'
                  onChange={(e) =>
                    this.setState({ challenge: Utils.safeParseEventValue(e) })
                  }
                />
              </>
            </div>

            <ModalHR />
            <div className='modal-footer'>
              <Button className="mr-2" theme='secondary' onClick={closeModal}>
                Cancel
              </Button>
              <Button
                id='confirm-remove-feature-btn'
                disabled={this.state.challenge != projectFlag.name}
                theme='primary'
              >
                Confirm changes
              </Button>
            </div>
          </form>
        )}
      </ProjectProvider>
    )
  }
}

ConfirmRemoveFeature.propTypes = {}

module.exports = ConfirmRemoveFeature
