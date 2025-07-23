import React from 'react'

interface OrganisationUsersTableHeaderProps {
  widths: number[]
}

const OrganisationUsersTableHeader: React.FC<
  OrganisationUsersTableHeaderProps
> = ({ widths }) => {
  return (
    <Row className='table-header'>
      <Flex className='table-column px-3'>User</Flex>
      <div
        className='table-column'
        style={{
          minWidth: widths[0],
        }}
      >
        Role
      </div>
      <div
        style={{
          width: widths[1],
        }}
        className='table-column'
      >
        Last logged in
      </div>
      <div
        style={{
          width: widths[2],
        }}
        className='table-column text-center'
      >
        Actions
      </div>
    </Row>
  )
}

export default OrganisationUsersTableHeader
