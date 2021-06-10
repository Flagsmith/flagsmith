import React from 'react';

function SegmentsIcon({ width, height, fill, className }) {
    return (
        <svg
          className={className}
          viewBox="0 0 21 21"
        >
            <path
              d="M21.112 11.52H11.62l6.321 6.321c.242.242.64.261.888.027a9.58 9.58 0 002.925-5.634c.054-.379-.26-.714-.642-.714zm-.634-2.592A9.623 9.623 0 0011.552 0c-.365-.025-.672.283-.672.648V9.6h8.95c.366 0 .674-.306.648-.671zM8.96 11.52V2.028c0-.382-.336-.696-.714-.642-4.766.673-8.41 4.838-8.24 9.829.174 5.125 4.587 9.328 9.715 9.264a9.525 9.525 0 005.41-1.761c.317-.224.337-.69.063-.963L8.96 11.52z"
              fill="#FFF"
              fillRule="evenodd"
            />
        </svg>
    );
}

export default SegmentsIcon;
