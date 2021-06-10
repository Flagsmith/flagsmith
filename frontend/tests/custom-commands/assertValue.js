module.exports.command = async function (id, value, callback) {
    const res = await this.getValue(id);
    this.assert.equal(res.value, value);
    return this;
};
