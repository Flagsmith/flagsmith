import React from 'react';

function DocumentationIcon({ width, height, fill, className }) {
    return (
        <svg
          className={className} width={width || '100%'} height={height}
          viewBox="0 0 16 21"
        >
            <path
              d="M8.96 5.44V0h-8A.958.958 0 000 .96v18.56c0 .532.428.96.96.96H14.4c.532 0 .96-.428.96-.96V6.4H9.92a.963.963 0 01-.96-.96zm2.56 9.44c0 .264-.216.48-.48.48H4.32a.481.481 0 01-.48-.48v-.32c0-.264.216-.48.48-.48h6.72c.264 0 .48.216.48.48v.32zm0-2.56c0 .264-.216.48-.48.48H4.32a.481.481 0 01-.48-.48V12c0-.264.216-.48.48-.48h6.72c.264 0 .48.216.48.48v.32zm0-2.88v.32c0 .264-.216.48-.48.48H4.32a.481.481 0 01-.48-.48v-.32c0-.264.216-.48.48-.48h6.72c.264 0 .48.216.48.48zm3.84-4.564v.244h-5.12V0h.244c.256 0 .5.1.68.28L15.08 4.2c.18.18.28.424.28.676z"
              fill="#63f"
              fillRule="evenodd"
            />
        </svg>
    );
}

export default DocumentationIcon;
