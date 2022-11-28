const _data = require("../../common/data/base/_data");
let promise;
module.exports = ()=> {
    if (!promise) {
        promise =  _data.get("/version")
            .then((res)=>{
                //do this so that the version is always accessible by typing flagsmithVersion as a last resort
                global.flagsmithVersion = res;
                return res;
            })
    }
    return promise
}
