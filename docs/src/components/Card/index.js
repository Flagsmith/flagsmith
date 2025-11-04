import React, { CSSProperties } from 'react'; // CSSProperties allows inline styling with better type checking.
import clsx from 'clsx'; // clsx helps manage conditional className names in a clean and concise manner.
const Card = ({
  className, // Custom classes for the container card
  style, // Custom styles for the container card
  children, // Content to be included within the card
  shadow, // Used to add shadow under your card. Expected values are: low (lw), medium (md), tall (tl)
}) => {
  const cardShadow = shadow ? `item shadow--${shadow}` : '';
  return (
    <div className={clsx('card', className, cardShadow)} style={style}>
      {children}
    </div>
  );
};
export default Card;