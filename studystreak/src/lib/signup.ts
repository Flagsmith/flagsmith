export type SignupInput = { name: string; email: string };
export type SignupErrors = Partial<Record<keyof SignupInput, string>>;
export type SignupValidation = { ok: true; value: SignupInput } | { ok: false; errors: SignupErrors };

export const NAME_MAX_LENGTH = 80;
const EMAIL_MAX_LENGTH = 254;
const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function validateSignup(input: unknown): SignupValidation {
    const fields = typeof input === 'object' && input !== null ? (input as Record<string, unknown>) : {};
    const name = typeof fields.name === 'string' ? fields.name.trim() : '';
    const email = typeof fields.email === 'string' ? fields.email.trim() : '';
    const errors: SignupErrors = {};

    if (!name) {
        errors.name = 'Enter your name.';
    } else if (name.length > NAME_MAX_LENGTH) {
        errors.name = `Use ${NAME_MAX_LENGTH} characters or fewer.`;
    }
    if (!email) {
        errors.email = 'Enter your email address.';
    } else if (email.length > EMAIL_MAX_LENGTH || !EMAIL_PATTERN.test(email)) {
        errors.email = 'Enter a valid email address.';
    }

    return Object.keys(errors).length > 0 ? { ok: false, errors } : { ok: true, value: { name, email } };
}
