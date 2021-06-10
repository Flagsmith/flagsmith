import React from 'react';

function CaretRightIcon({ width, height, fill, className }) {
    return (
      <svg className={className} width={9} height={10} viewBox="0 0 9 10">
        <path
          d="M.133 9.263V1.474c0-.539.732-.808 1.16-.427L5.678 4.94a.56.56 0 010 .857L1.294 9.69c-.43.381-1.161.112-1.161-.427z"
          fill="#000"
          fillRule="evenodd"
        />
      </svg>
    );
}

export default CaretRightIcon;
