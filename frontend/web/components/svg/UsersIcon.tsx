import React from 'react'

interface UsersIconProps {
  className?: string
  width?: number
  fill?: string
}

const UsersIcon: React.FC<UsersIconProps> = ({ className, fill, width }) => (
  <svg className={className} width={width} viewBox='0 0 26 18'>
    <path
      d='M7.68 8.96a4.478 4.478 0 004.48-4.48A4.478 4.478 0 007.68 0 4.478 4.478 0 003.2 4.48a4.478 4.478 0 004.48 4.48zm3.072 1.28h-.332c-.832.4-1.756.64-2.74.64-.984 0-1.904-.24-2.74-.64h-.332A4.61 4.61 0 000 14.848V16c0 1.06.86 1.92 1.92 1.92h11.52c1.06 0 1.92-.86 1.92-1.92v-1.152a4.61 4.61 0 00-4.608-4.608zM19.2 8.96a3.841 3.841 0 000-7.68 3.841 3.841 0 000 7.68zm1.92 1.28h-.152a5.39 5.39 0 01-1.768.32 5.39 5.39 0 01-1.768-.32h-.152c-.816 0-1.568.236-2.228.616.976 1.052 1.588 2.448 1.588 3.992v1.536c0 .088-.02.172-.024.256h7.064c1.06 0 1.92-.86 1.92-1.92a4.478 4.478 0 00-4.48-4.48z'
      fill={fill || '#FFF'}
      fillRule='nonzero'
    />
  </svg>
)

export default UsersIcon
