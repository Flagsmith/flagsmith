exports.command = function (id, val) {
    this.waitForElementVisible(id)
        .setValue(id, val);

    return this;
};
