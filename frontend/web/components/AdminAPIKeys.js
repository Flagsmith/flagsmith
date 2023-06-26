import React, { PureComponent } from 'react'
import DatePicker from 'react-datepicker'
import data from 'common/data/base/_data'
import InfoMessage from './InfoMessage'
import Token from './Token'
import JSONReference from './JSONReference'

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
        {!this.state.key && (
          <div>
            <Flex className='mb-4 mr-3'>
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
            <Flex className='mb-4 mr-3'>
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
                    theme='secondary'
                    size='small'
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
        <div className='container'>
          <div className='text-right'>
            {this.state.key ? (
              <div />
            ) : (
              <Button
                onClick={this.submit}
                data-test='create-feature-btn'
                id='create-feature-btn'
                disabled={this.state.isSaving || !this.state.name}
                size='small'
              >
                {this.state.isSaving ? 'Creating' : 'Create'}
              </Button>
            )}
          </div>
        </div>
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
      <div>Are you sure?</div>,
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
        <Row space className='mt-4'>
          <h3>Terraform API Keys</h3>
          <Button onClick={this.createAPIKey} disabled={this.state.isLoading}>
            Create Terraform API Key
          </Button>
          <p>
            Terraform API keys are used to authenticate with the Admin API.{' '}
            <Button
              theme='text'
              href='https://docs.flagsmith.com/integrations/terraform#terraform-api-key'
              target='_blank'
            >
              Learn about Terraform Keys.
            </Button>
          </p>
        </Row>
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
