import React from "react";


class _Headway extends React.Component {

componentDidMount() {
    try {
        Headway.init({
            enabled: true,
            selector: "#headway",
            account: "yErY2x"
        });

    } catch (e) {}

}

    render() {

        return (
            <Row id="headway" className={this.props.className}
            >
            </Row>
        );
    }
}


export default _Headway;
