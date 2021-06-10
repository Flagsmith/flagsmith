import React from 'react';

function PlusIcon({ width, height, fill, className }) {
    return (
        <svg
          width={width}
          className={className}
          viewBox="0 0 15 13"
        >
            <path
              d="M13.8 5.5H8.4V.55C8.4.246 8.132 0 7.8 0H6.6c-.332 0-.6.246-.6.55V5.5H.6c-.332 0-.6.246-.6.55v1.1c0 .304.268.55.6.55H6v4.95c0 .304.268.55.6.55h1.2c.332 0 .6-.246.6-.55V7.7h5.4c.332 0 .6-.246.6-.55v-1.1c0-.304-.268-.55-.6-.55z"
              fill="#FFF"
              fillRule="nonzero"
            />
        </svg>
    );
}

export default PlusIcon;
