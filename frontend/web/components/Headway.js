import React from "react";
import SparklesIcon from "./svg/SparklesIcon";


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
            <Row className={this.props.className}
            >
                <Row onClick={()=>{
                    Headway.show()
                }}>
                    <SparklesIcon />
                    Updates
                </Row>
                <span id="headway"/>
            </Row>
        );
    }
}

export default _Headway;
