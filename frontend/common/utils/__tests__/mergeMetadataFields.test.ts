import { mergeMetadataFields } from 'common/utils/mergeMetadataFields'
import {
  MetadataField,
  MetadataModelField,
  PagedResponse,
} from 'common/types/responses'

const createFieldList = (
  fields: Partial<MetadataField>[],
): PagedResponse<MetadataField> => ({
  results: fields.map((f, idx) => ({
    description: 'Test description',
    id: idx + 1,
    name: `Field ${idx + 1}`,
    organisation: 1,
    type: 'str',
    ...f,
  })) as MetadataField[],
})

const createModelFieldList = (
  modelFields: Partial<MetadataModelField>[],
): PagedResponse<MetadataModelField> => ({
  results: modelFields.map((mf, idx) => ({
    content_type: 100,
    field: idx + 1,
    id: `${idx + 10}`,
    is_required_for: [],
    ...mf,
  })) as MetadataModelField[],
})

describe('mergeMetadataFields', () => {
  it('merges field definitions with existing values', () => {
    const fieldList = createFieldList([{ id: 1, name: 'Field 1' }])
    const modelFieldList = createModelFieldList([
      { content_type: 100, field: 1, id: '10', is_required_for: [] },
    ])
    const entityData = {
      metadata: [{ field_value: 'existing value', model_field: '10' }],
    }

    const result = mergeMetadataFields(
      fieldList,
      modelFieldList,
      entityData,
      100,
    )

    expect(result).toHaveLength(1)
    expect(result[0].field_value).toBe('existing value')
    expect(result[0].hasValue).toBe(true)
  })

  it('sets empty field_value when no existing value or null entity', () => {
    const fieldList = createFieldList([{ id: 1, name: 'Field 1' }])
    const modelFieldList = createModelFieldList([
      { content_type: 100, field: 1, id: '10', is_required_for: [] },
    ])

    const result = mergeMetadataFields(fieldList, modelFieldList, null, 100)

    expect(result[0].field_value).toBe('')
    expect(result[0].hasValue).toBe(false)
  })

  it('marks field as required when is_required_for has entries', () => {
    const fieldList = createFieldList([{ id: 1, name: 'Required Field' }])
    const modelFieldList = createModelFieldList([
      {
        content_type: 100,
        field: 1,
        id: '10',
        is_required_for: [{ content_type: 50 }],
      },
    ])

    const result = mergeMetadataFields(fieldList, modelFieldList, null, 100)

    expect(result[0].isRequiredFor).toBe(true)
  })

  it('sorts required fields first', () => {
    const fieldList = createFieldList([
      { id: 1, name: 'Optional' },
      { id: 2, name: 'Required' },
    ])
    const modelFieldList = createModelFieldList([
      { content_type: 100, field: 1, id: '10', is_required_for: [] },
      {
        content_type: 100,
        field: 2,
        id: '11',
        is_required_for: [{ content_type: 50 }],
      },
    ])

    const result = mergeMetadataFields(fieldList, modelFieldList, null, 100)

    expect(result[0].name).toBe('Required')
    expect(result[1].name).toBe('Optional')
  })
})
