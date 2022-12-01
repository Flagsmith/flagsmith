const _data = require("../../common/data/base/_data");
let promise;
module.exports = ()=> {
    if (!promise) {
        promise =  Promise.all([_data.get("/version").catch(()=>({})), _data.get(`${Project.api.replace("api/v1/","")}version`).catch(()=>({}))])
            .then(([frontend,backend])=>{
                const res = { frontend, backend };
                //do this so that the version is always accessible by typing flagsmithVersion as a last resort

                const tag = backend?.image_tag || "Unknown"
                const backend_sha = backend?.ci_commit_sha || "Unknown"
                const frontend_sha = frontend?.ci_commit_sha || "Unknown"

                res.tag = tag;
                res.backend_sha = backend_sha;
                res.frontend_sha = frontend_sha;
                global.flagsmithVersion = res;
                return res;
            })
    }
    return promise
}
