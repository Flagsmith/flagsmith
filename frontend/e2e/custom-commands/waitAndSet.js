exports.command = function (selector, val) {
    const { RIGHT_ARROW, BACK_SPACE } = this.Keys;
    this.waitForElementVisible(selector);
    return this.getValue(selector, (result) => {
        const chars = result.value.split('');
        // Make sure we are at the end of the input
        chars.forEach(() => this.setValue(selector, RIGHT_ARROW));
        // Delete all the existing characters
        chars.forEach(() => this.setValue(selector, BACK_SPACE));

        this.setValue(selector, val);

        return this;
    });
};
