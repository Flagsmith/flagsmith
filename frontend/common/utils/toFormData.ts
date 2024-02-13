type Serializeable =
  | string
  | number
  | boolean
  | null
  | Date
  | File
  | { [x: string | number]: Serializeable }
  | Array<Serializeable>

export default function toFormData(
  data: Serializeable,
  parentKey = '',
  formData: FormData = new FormData(),
): FormData {
  if (typeof data === 'string') {
    formData.append(parentKey, data)
  } else if (typeof data === 'number') {
    formData.append(parentKey, data.toString())
  } else if (typeof data === 'boolean') {
    formData.append(parentKey, data ? 'true' : 'false')
  } else if (data === null) {
    // formData.append(parentKey, 'null')
  } else if (data instanceof Date) {
    formData.append(parentKey, data.toISOString())
  } else if (data instanceof File) {
    formData.append(parentKey, data)
  } else {
    // Arrays and objects
    Object.entries(data).forEach((entry: [string | number, Serializeable]) => {
      const [key, value] = entry
      toFormData(
        value,
        parentKey ? `${parentKey}[${key}]` : key.toString(),
        formData,
      )
    })
  }

  return formData
}
