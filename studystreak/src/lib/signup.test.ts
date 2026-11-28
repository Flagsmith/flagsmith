import { describe, expect, it } from 'vitest';
import { validateSignup } from './signup';

describe('validateSignup', () => {
    it('accepts and trims a valid signup', () => {
        expect(validateSignup({ name: '  Asha  ', email: ' asha@example.com ' })).toEqual({
            ok: true,
            value: { name: 'Asha', email: 'asha@example.com' },
        });
    });

    it.each([
        [{}, ['name', 'email']],
        [{ name: '   ', email: 'asha@example.com' }, ['name']],
        [{ name: 'Asha', email: 'not-an-email' }, ['email']],
        [{ name: 'Asha', email: 'asha@example' }, ['email']],
        [{ name: 'A'.repeat(81), email: 'asha@example.com' }, ['name']],
        [{ name: 'Asha', email: `${'a'.repeat(250)}@example.com` }, ['email']],
        [{ name: 42, email: ['asha@example.com'] }, ['name', 'email']],
        [{ name: 'Asha', email: 'alice@.example.com' }, ['email']],
        [{ name: 'Asha', email: 'alice@example..com' }, ['email']],
        [{ name: 'Asha', email: 'alice@example.com.' }, ['email']],
        [{ name: 'Asha', email: 'alice@-example.com' }, ['email']],
        [{ name: 'Asha', email: 'alice@example-.com' }, ['email']],
        [{ name: 'Asha', email: 'alice@exa_mple.com' }, ['email']],
        [{ name: 'Asha', email: 'alice@@example.com' }, ['email']],
        [{ name: 'Asha', email: 'al@ice@example.com' }, ['email']],
        [{ name: 'Asha', email: '.alice@example.com' }, ['email']],
        [{ name: 'Asha', email: 'alice.@example.com' }, ['email']],
        [{ name: 'Asha', email: 'al..ice@example.com' }, ['email']],
        [{ name: 'Asha', email: `alice@${'a'.repeat(64)}.com` }, ['email']],
    ])('rejects %j', (input, invalidFields) => {
        const result = validateSignup(input);
        expect(result.ok).toBe(false);
        expect(Object.keys(result.ok ? {} : result.errors).sort()).toEqual([...invalidFields].sort());
    });

    it.each([
        'asha@example.com',
        'a.sha+demo@mail.example.co.uk',
        'asha@xn--bcher-kva.example',
        'asha@bücher.de',
        'a@b.io',
    ])('accepts the well-formed address %j', (email) => {
        expect(validateSignup({ name: 'Asha', email }).ok).toBe(true);
    });

    it.each([null, 'name=Asha', 7])('rejects a non-object body (%j)', (input) => {
        expect(validateSignup(input).ok).toBe(false);
    });
});
