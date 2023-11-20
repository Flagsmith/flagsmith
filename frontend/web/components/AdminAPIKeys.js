import React, { PureComponent } from 'react'
import data from 'common/data/base/_data'
import InfoMessage from './InfoMessage'
import Token from './Token'
import JSONReference from './JSONReference'
import Button from './base/forms/Button'
import DateSelect from './DateSelect'
import Icon from './Icon'

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
      <>
        <div className='modal-body flex flex-column flex-fill px-4'>
          {!this.state.key && (
            <div>
              <Flex className='mb-3 mt-4'>
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
                  <label>Expiry</label>
                </div>
                <DateSelect
                  onChange={(e) => {
                    this.setState({
                      expiry_date: e.toISOString(),
                    })
                  }}
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
            </div>
          )}

          {this.state.key && (
            <div className='mb-4'>
              <InfoMessage>
                Please keep a note of your API key once it's created, we do not
                store it.
              </InfoMessage>

              <Token show token={this.state.key} />
            </div>
          )}
          {this.state.key ? (
            <div />
          ) : (
            <>
              <div className='modal-footer my-5 p-0'>
                <Button
                  disabled={!this.state.expiry_date}
                  onClick={() => this.setState({ expiry_date: null })}
                  theme='secondary'
                  className='mr-2'
                >
                  Clear Date
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
      </>
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
      'p-0 side-modal',
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
        <Column className='my-4 ml-0 col-md-6'>
          <h5 className='mb-1'>Terraform API Keys</h5>
          <p className='mb-0 fs-small lh-sm'>
            Terraform API keys are used to authenticate with the Admin API.
          </p>
          <div className='mb-4 fs-small lh-sm'>
            <Button
              theme='text'
              href='https://docs.flagsmith.com/integrations/terraform#terraform-api-key'
              target='_blank'
              className='fw-normal'
            >
              Learn about Terraform Keys.
            </Button>
          </div>
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
          <PanelSearch
            className='no-pad'
            title='API Keys'
            items={apiKeys}
            header={
              <Row className='table-header'>
                <Flex className='table-column px-3'>API Keys</Flex>
                <Flex className='table-column'>Created</Flex>
                <div
                  className='table-column text-center'
                  style={{ width: '80px' }}
                >
                  Remove
                </div>
              </Row>
            }
            renderRow={(v) =>
              !v.revoked && (
                <Row className='list-item' key={v.id}>
                  <Flex className='table-column px-3'>
                    <div className='font-weight-medium mb-1'>{v.name}</div>
                    <div className='list-item-subtitle'>
                      <div>{v.prefix}*****************</div>
                    </div>
                  </Flex>
                  <Flex className='table-column fs-small lh-sm'>
                    {moment(v.created).format('Do MMM YYYY HH:mma')}
                  </Flex>
                  <div
                    className='table-column  text-center'
                    style={{ width: '80px' }}
                  >
                    <Button
                      onClick={() => this.remove(v)}
                      className='btn btn-with-icon'
                    >
                      <Icon name='trash-2' width={20} fill='#656D7B' />
                    </Button>
                  </div>
                </Row>
              )
            }
          />
        )}
      </div>
    )
  }
}
