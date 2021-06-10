import React from 'react';

function CaretDownIcon({ width, height, fill, className }) {
    return (
        <div style={{ paddingRight: 2 }}>
            <svg
              style={{ marginLeft: -2 }} className={className} width={9}
              height={10} viewBox="0 0 9 6"
            >
                <path
                  d="M.6 0h7.72c.533 0 .8.645.422 1.023L4.884 4.884a.601.601 0 01-.849 0L.177 1.023A.599.599 0 01.6 0z"
                  fill="#FFF"
                  fillRule="evenodd"
                />
            </svg>
        </div>

    );
}

export default CaretDownIcon;
