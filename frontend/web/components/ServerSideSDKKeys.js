import React, { Component } from 'react'
import _data from 'common/data/base/_data'
import ProjectStore from 'common/stores/project-store'
import Token from './Token'
import ModalHR from './modals/ModalHR'

class CreateServerSideKeyModal extends Component {
  state = {}

  componentDidMount() {
    setTimeout(() => {
      document.getElementById('jsTokenName').focus()
    }, 500)
  }

  onSubmit = (e) => {
    Utils.preventDefault(e)
    if (this.state.name) {
      this.setState({
        isSaving: true,
      })
      this.props.onSubmit(this.state.name)
    }
  }

  render() {
    return (
      <div>
        <form onSubmit={this.onSubmit}>
          <div className='modal-body'>
            <div className='mb-2'>
              This will create a Server-side Environment Key for the environment{' '}
              <strong>
                {ProjectStore.getEnvironment(this.props.environmentId).name}
              </strong>
              .
            </div>
            <InputGroup
              title='Key Name'
              placeholder='New Key'
              className='mb-2'
              id='jsTokenName'
              inputProps={{
                className: 'full-width modal-input',
              }}
              onChange={(e) =>
                this.setState({ name: Utils.safeParseEventValue(e) })
              }
            />
          </div>
          <ModalHR />
          <div className='modal-footer'>
            <Button onClick={closeModal} theme='secondary' className={'mr-2'}>
              Cancel
            </Button>
            <Button
              type='submit'
              disabled={!this.state.name || this.state.isSaving}
            >
              Create
            </Button>
          </div>
        </form>
      </div>
    )
  }
}

class ServerSideSDKKeys extends Component {
  state = {
    isLoading: true,
  }

  static propTypes = {
    environmentId: propTypes.string.isRequired,
  }

  componentDidMount() {
    this.fetch(this.props.environmentId)
  }

  componentDidUpdate(prevProps) {
    if (prevProps.environmentId !== this.props.environmentId) {
      this.fetch(this.props.environmentId)
    }
  }

  createKey = () => {
    openModal(
      'Create Server-side Environment Keys',
      <CreateServerSideKeyModal
        environmentId={this.props.environmentId}
        onSubmit={(name) => {
          _data
            .post(
              `${Project.api}environments/${this.props.environmentId}/api-keys/`,
              { name },
            )
            .then(() => this.fetch(this.props.environmentId))
            .finally(() => {
              closeModal()
            })
        }}
      />,
      'p-0',
    )
  }

  remove = (id, name) => {
    openConfirm(
      'Delete Server-side Environment Keys',
      <div>
        The key <strong>{name}</strong> will be permanently deleted, are you
        sure?
      </div>,
      () => {
        this.setState({ isSaving: true })
        _data
          .delete(
            `${Project.api}environments/${this.props.environmentId}/api-keys/${id}`,
          )
          .then(() => this.fetch(this.props.environmentId))
          .finally(() => {
            this.setState({ isSaving: false })
          })
      },
    )
  }

  fetch = (environmentId) => {
    this.setState({ isLoading: true })
    return _data
      .get(`${Project.api}environments/${environmentId}/api-keys/`)
      .then((keys) => {
        this.setState({ isLoading: false, keys })
      })
      .catch(() => {
        this.setState({ isLoading: false })
      })
  }

  render() {
    return (
      <FormGroup className='m-y-3'>
        <Row className='mb-3' space>
          <div className='col-md-8 pl-0'>
            <h5 className='m-b-0'>Server-side Environment Keys</h5>
            <p className='fs-small lh-sm'>
              Flags can be evaluated locally within your own Server environments
              using our{' '}
              <Button
                theme='text'
                href='https://docs.flagsmith.com/clients/overview'
                target='__blank'
              >
                Server-side Environment Keys
              </Button>
              .
            </p>
            <p className='fs-small lh-sm'>
              Server-side SDKs should be initialised with a Server-side
              Environment Key.
            </p>
          </div>
          <div className='col-md-4 pr-0'>
            <Button
              onClick={this.createKey}
              className='float-right'
              disabled={this.state.isSaving}
            >
              Create Server-side Environment Key
            </Button>
          </div>
        </Row>
        {this.state.isLoading && (
          <div className='text-center'>
            <Loader />
          </div>
        )}
        {this.state.keys && !!this.state.keys.length && (
          <PanelSearch
            id='org-members-list'
            title='Server-side Environment Keys'
            className='no-pad'
            items={this.state.keys}
            filterRow={(item, search) => {
              const strToSearch = `${item.name}`
              return (
                strToSearch.toLowerCase().indexOf(search.toLowerCase()) !== -1
              )
            }}
            renderRow={({ id, key, name }) => (
              <div className='list-item'>
                <Row>
                  <Flex>{name}</Flex>
                  <Token style={{ width: 280 }} token={key} />
                  <button
                    onClick={() => this.remove(id, name)}
                    disabled={this.state.isSaving}
                    id='remove-feature'
                    className='btn btn--with-icon'
                  >
                    <RemoveIcon />
                  </button>
                </Row>
              </div>
            )}
          />
        )}
      </FormGroup>
    )
  }
}
export default ServerSideSDKKeys
