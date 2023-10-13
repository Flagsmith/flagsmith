import React, { useState } from 'react'
import Icon from 'components/Icon'

type CreateMetadataType = {
  isEdit: boolean
}

type MetadataType = {
  id: int
  value: string
  label: string
}

const CreateMetadata: FC<CreateMetadataType> = ({ isEdit }) => {
  const metadataTypes: MetadataType = [
    { id: 1, label: 'int', value: 'int' },
    { id: 2, label: 'string', value: 'str' },
    { id: 3, label: 'boolean', value: 'bool' },
    { id: 4, label: 'url', value: 'url' },
    { id: 5, label: 'multiline string', value: 'multiline_str' },
  ]
  const identities = [
    { id: 1, value: 'Environment' },
    { id: 2, value: 'Segment' },
    { id: 3, value: 'Flag' },
  ]
  const [typeValue, setTypeValue] = useState<string>('')
  const [name, setName] = useState<string>('')
  const [description, setDescription] = useState<string>('')
  const [enable, setEnable] = useState<boolean>(false)
  const [required, setRequired] = useState<boolea>(false)

  return (
    <div className='create-feature-tab px-3'>
      <InputGroup
        title='Name'
        className='mb-4 mt-2'
        inputProps={{
          className: 'full-width',
          name: 'Name',
        }}
        value={name}
        onChange={(event: React.ChangeEvent<HTMLInputElement>) => {
          setName(Utils.safeParseEventValue(event))
        }}
        type='text'
        id='metadata-name'
        placeholder='FL-124'
      />
      <InputGroup
        value={description}
        data-test='metadata-desc'
        className='mb-4'
        inputProps={{
          className: 'full-width',
          name: 'metadata-desc',
        }}
        onChange={(event: React.ChangeEvent<HTMLInputElement>) => {
          setDescription(Utils.safeParseEventValue(event))
        }}
        type='text'
        title={'Description (optional)'}
        placeholder='This is a metadata description'
      />
      <Select
        value={typeValue}
        placeholder='Select a metadata type'
        options={metadataTypes}
        onChange={(label) => setTypeValue(label)}
        className='mb-4 react-select'
      />
      {/* {isEdit && (
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-evenly',
            marginLeft: '20px',
          }}
        >
          <h6>Enable</h6> <h6>Required</h6>
        </div>
      )} */}
      {/* {isEdit &&
        identities.map((i, index) => (
          <FormGroup className='mb-5 setting' key={index}>
            <Row
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                width: '400px',
              }}
            >
              <h6>{i.value}</h6>
              <Switch
                checked={enable}
                onChange={() => setEnable(!enable)}
                className='ml-0'
              />
              <Switch
                checked={required}
                onChange={() => setRequired(!required)}
                className='ml-0'
              />
            </Row>
          </FormGroup>
        ))} */}

      {isEdit && (
        <div className='identities-table mb-3'>
          <div className='identities-row'>
            <div className='identities-cell identities-header'>Entities</div>
            <div className='identities-cell identities-header'>Enabled</div>
            <div className='identities-cell identities-header'>Required</div>
          </div>
          <div className='identities-row'>
            <div className='identities-cell identities-header'>Environment</div>
            <div className='identities-cell'>
              <Switch
                checked={enable}
                onChange={() => setEnable(!enable)}
                className='ml-0'
              />
            </div>
            <div className='identities-cell'>
              <Switch
                checked={required}
                onChange={() => setRequired(!required)}
                className='ml-0'
              />
            </div>
          </div>
          <div className='identities-row'>
            <div className='identities-cell identities-header'>Segment</div>
            <div className='identities-cell'>
              <Switch
                checked={enable}
                onChange={() => setEnable(!enable)}
                className='ml-0'
              />
            </div>
            <div className='identities-cell'>
              <Switch
                checked={required}
                onChange={() => setRequired(!required)}
                className='ml-0'
              />
            </div>
          </div>
          <div className='identities-row'>
            <div className='identities-cell identities-header'>Flag</div>
            <div className='identities-cell'>
              <Switch
                checked={enable}
                onChange={() => setEnable(!enable)}
                className='ml-0'
              />
            </div>
            <div className='identities-cell'>
              <Switch
                checked={required}
                onChange={() => setRequired(!required)}
                className='ml-0'
              />
            </div>
          </div>
        </div>
      )}
      <Button onClick={() => this.createMetadata()} className='float-right'>
        {isEdit ? 'Update Metadata' : 'Create Metadata'}
      </Button>
    </div>
  )
}

export default CreateMetadata
