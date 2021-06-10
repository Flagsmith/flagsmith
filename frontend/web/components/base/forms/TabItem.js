const TabItem = props => (
    props.children || null
);
TabItem.displayName = 'TabItem';
TabItem.propTypes = {
    children: OptionalNode,
};
module.exports = TabItem;
