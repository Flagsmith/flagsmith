import React from "react";


class _Headway extends React.Component {

componentDidMount() {
    try {
        Headway.init({
            enabled: true,
            selector: "#headway",
            account: "yErY2x"
        });
        Headway.show()

    } catch (e) {}

}

    render() {

        return (
            <span
                onLoad={()=>{
                    var config = {
                        selector: ".js-headway",
                        account: "yErY2x"
                    };
                    Headway.init(config);
                }}
                href="https://docs.flagsmith.com"
                target="_blank" id="headway" className={this.props.className}
            >
            </span>
        );
    }
}


export default _Headway;
