import React, { PureComponent } from 'react'
import DatePicker from 'react-datepicker'
import data from 'common/data/base/_data'
import InfoMessage from './InfoMessage'
import Token from './Token'
import JSONReference from './JSONReference'
import ModalHR from './modals/ModalHR'
import Button from './base/forms/Button'

export class CreateAPIKey extends PureComponent {
  state = {
    expiry_date: null,
    key: '',
    name: '',
  }

  submit = () => {
    this.setState({ isSaving: true })
    data
      .post(
        `${Project.api}organisations/${
          AccountStore.getOrganisation().id
        }/master-api-keys/`,
        {
          expiry_date: this.state.expiry_date,
          name: this.state.name,
          organisation: AccountStore.getOrganisation().id,
        },
      )
      .then((res) => {
        this.setState({
          isSaving: false,
          key: res.key,
        })
        this.props.onSuccess()
      })
  }

  render() {
    return (
      <div>
        <div className='modal-body'>
          {!this.state.key && (
            <div>
              <Flex className='mb-4'>
                <div>
                  <label>Name</label>
                </div>
                <Input
                  value={this.state.name}
                  onChange={(e) =>
                    this.setState({ name: Utils.safeParseEventValue(e) })
                  }
                  isValid={!!this.state.name}
                  type='text'
                  inputClassName='input--wide'
                  placeholder='e.g. Admin API Key'
                />
              </Flex>
              <Flex>
                <div>
                  <label>Expiry (Leave empty for no expiry)</label>
                </div>
                <Row>
                  <Flex>
                    <DatePicker
                      minDate={new Date()}
                      onChange={(e) => {
                        this.setState({
                          expiry_date: e.toISOString(),
                        })
                      }}
                      showTimeInput
                      selected={
                        this.state.expiry_date
                          ? moment(this.state.expiry_date)._d
                          : null
                      }
                      value={
                        this.state.expiry_date
                          ? `${moment(this.state.expiry_date).format(
                              'Do MMM YYYY hh:mma',
                            )}`
                          : 'Never'
                      }
                    />
                  </Flex>

                  <div className='ml-2'>
                    <Button
                      disabled={!this.state.expiry_date}
                      onClick={() => this.setState({ expiry_date: null })}
                      theme='text'
                    >
                      Clear
                    </Button>
                  </div>
                </Row>
              </Flex>
            </div>
          )}

          {this.state.key && (
            <div className='mb-4'>
              <InfoMessage>
                Please keep a note of your API key once it's created, we do not
                store it.
              </InfoMessage>

              <Token show style={{ width: '435px' }} token={this.state.key} />
            </div>
          )}
        </div>

        {this.state.key ? (
          <div />
        ) : (
          <>
            <ModalHR />
            <div className='modal-footer'>
              <Button onClick={closeModal} theme='secondary' className='mr-2'>
                Cancel
              </Button>
              <Button
                onClick={this.submit}
                disabled={this.state.isSaving || !this.state.name}
              >
                {this.state.isSaving ? 'Creating' : 'Create'}
              </Button>
            </div>
          </>
        )}
      </div>
    )
  }
}

export default class AdminAPIKeys extends PureComponent {
  static displayName = 'TheComponent'

  state = {
    isLoading: true,
  }

  static propTypes = {}

  componentDidMount() {
    this.fetch()
  }

  createAPIKey = () => {
    openModal(
      'New Admin API Key',
      <CreateAPIKey
        onSuccess={() => {
          this.setState({ isLoading: true })
          this.fetch()
        }}
      />,
      'p-0',
    )
  }

  fetch = () => {
    data
      .get(
        `${Project.api}organisations/${
          AccountStore.getOrganisation().id
        }/master-api-keys/`,
      )
      .then((res) => {
        this.setState({
          apiKeys: res,
          isLoading: false,
        })
      })
  }

  remove = (v) => {
    openConfirm(
      'Are you sure?',
      <div>
        This will revoke the API key <strong>{v.name}</strong> ({v.prefix}
        *****************). This change cannot be reversed.
      </div>,
      () => {
        data
          .delete(
            `${Project.api}organisations/${
              AccountStore.getOrganisation().id
            }/master-api-keys/${v.prefix}/`,
          )
          .then(() => {
            this.fetch()
          })
      },
    )
  }

  render() {
    const apiKeys = this.state.apiKeys && this.state.apiKeys.results
    return (
      <div>
        <JSONReference
          className='mt-4'
          hideCondensedButton
          title={'Terraform API Keys'}
          json={apiKeys}
        />
        <Column className='mt-4 ml-0'>
          <h5 className='mb-0'>Terraform API Keys</h5>
          <p className='mb-4 fs-small lh-sm'>
            Terraform API keys are used to authenticate with the Admin API.{' '}
            <Button
              theme='text'
              href='https://docs.flagsmith.com/integrations/terraform#terraform-api-key'
              target='_blank'
            >
              Learn about Terraform Keys.
            </Button>
          </p>
          <Button onClick={this.createAPIKey} disabled={this.state.isLoading}>
            Create Terraform API Key
          </Button>
        </Column>
        {this.state.isLoading && (
          <div className='text-center'>
            <Loader />
          </div>
        )}
        {!!apiKeys && !!apiKeys.length && (
          <Panel className='mt-4' title='API Keys'>
            {apiKeys &&
              apiKeys.map(
                (v) =>
                  !v.revoked && (
                    <div className='list-item' key={v.id}>
                      <Row>
                        <Flex>
                          <strong>{v.name}</strong>
                          <div className='list-item-footer faint'>
                            <div>{v.prefix}*****************</div>
                            <div>
                              Created{' '}
                              {moment(v.created).format('Do MMM YYYY HH:mma')}
                            </div>
                          </div>
                        </Flex>
                        <Button
                          onClick={() => this.remove(v)}
                          className='btn btn--with-icon ml-auto btn--remove'
                        >
                          <RemoveIcon />
                        </Button>
                      </Row>
                    </div>
                  ),
              )}
          </Panel>
        )}
      </div>
    )
  }
}
