import React from 'react';

function UserSettingsIcon({ width, height, className }) {
    return (
        <svg
          className={className} width={width || '100%'} height={height}
          viewBox="0 0 26 18"
        >
            <path
              d="M8.96 10.24A5.12 5.12 0 108.96 0a5.12 5.12 0 000 10.24zm3.584 1.28h-.668a6.97 6.97 0 01-5.832 0h-.668A5.377 5.377 0 000 16.896v1.664c0 1.06.86 1.92 1.92 1.92H16c1.06 0 1.92-.86 1.92-1.92v-1.664a5.377 5.377 0 00-5.376-5.376z"
              fill="#fff"
              fillRule="evenodd"
            />
        </svg>
    );
}

export default UserSettingsIcon;
