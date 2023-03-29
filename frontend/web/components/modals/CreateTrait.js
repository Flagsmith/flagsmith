import React, { Component } from 'react'
import Highlight from 'components/Highlight'
import Constants from 'common/constants'
import Format from 'common/utils/format'
import ErrorMessage from 'components/ErrorMessage'

const CreateTrait = class extends Component {
  static displayName = 'CreateTrait'

  constructor(props, context) {
    super(props, context)
    const {
      props: { id, trait_key, trait_value },
    } = this
    this.state = { id, trait_key, trait_value }
  }

  close() {
    closeModal()
  }

  onSave = () => {
    if (this.props.onSave) {
      this.props.onSave()
    }
    this.close()
  }

  componentDidMount = () => {
    if (!this.props.isEdit) {
      this.focusTimeout = setTimeout(() => {
        this.input.focus()
        this.focusTimeout = null
      }, 500)
    }
  }

  componentWillUnmount() {
    if (this.focusTimeout) {
      clearTimeout(this.focusTimeout)
    }
  }

  render() {
    const {
      props: { identity, isEdit, projectId },
    } = this
    const {
      state: { trait_key, trait_value },
    } = this
    const TRAITS_ID_MAXLENGTH = Constants.forms.maxLength.TRAITS_ID

    return (
      <ProjectProvider id={projectId}>
        {({ project }) => (
          <IdentityProvider onSave={this.onSave}>
            {({ error, isSaving }, { createTrait }) => (
              <form
                id='create-trait-modal'
                onSubmit={(e) => {
                  e.preventDefault()
                  this.save(createTrait, isSaving)
                }}
              >
                <FormGroup className='mb-3'>
                  <InputGroup
                    ref={(e) => (this.input = e)}
                    inputProps={{
                      className: 'full-width',
                      maxLength: TRAITS_ID_MAXLENGTH,
                      name: 'traitID',
                      readOnly: isEdit,
                    }}
                    value={trait_key}
                    onChange={(e) =>
                      this.setState({
                        trait_key: Format.enumeration
                          .set(Utils.safeParseEventValue(e))
                          .toLowerCase(),
                      })
                    }
                    isValid={trait_key && trait_key.length}
                    type='text'
                    title={isEdit ? 'Trait ID' : 'Trait ID*'}
                    placeholder='E.g. favourite_color'
                  />
                </FormGroup>
                <FormGroup className='mb-3'>
                  <InputGroup
                    textarea
                    inputProps={{ className: 'full-width', name: 'traitValue' }}
                    value={trait_value}
                    title='Value'
                    onChange={(e) =>
                      this.setState({
                        trait_value: Utils.getTypedValue(
                          Utils.safeParseEventValue(e),
                        ),
                      })
                    }
                    type='text'
                    placeholder="e.g. 'big', true, 1 "
                  />
                </FormGroup>

                {error && <ErrorMessage error={error} />}

                <p className='text-right faint-lg'>
                  This will {isEdit ? 'update' : 'create'} a user trait{' '}
                  <strong>{trait_key || ''}</strong> for the user{' '}
                  <strong>{identity}</strong> in
                  <strong>
                    {' '}
                    {
                      _.find(project.environments, {
                        api_key: this.props.environmentId,
                      }).name
                    }
                  </strong>
                </p>

                <FormGroup className='flag-example'>
                  <strong>Example SDK response:</strong>
                  <Highlight forceExpanded className='json no-pad'>
                    {JSON.stringify({ trait_key, trait_value })}
                  </Highlight>
                </FormGroup>

                <div className='text-right'>
                  {isEdit ? (
                    <Button
                      id='update-trait-btn'
                      disabled={isSaving || !trait_key}
                    >
                      {isSaving ? 'Creating' : 'Update Trait'}
                    </Button>
                  ) : (
                    <Button
                      id='create-trait-btn'
                      disabled={isSaving || !trait_key}
                    >
                      {isSaving ? 'Creating' : 'Create Trait'}
                    </Button>
                  )}
                </div>
              </form>
            )}
          </IdentityProvider>
        )}
      </ProjectProvider>
    )
  }

  save = (func) => {
    const {
      props: { environmentId, identity },
      state: { id, trait_key, trait_value },
    } = this
    func({
      environmentId,
      identity,
      trait: { id, trait_key, trait_value },
    })
  }
}

CreateTrait.propTypes = {}

module.exports = CreateTrait
