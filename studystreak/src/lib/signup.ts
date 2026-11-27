export type SignupInput = { name: string; email: string };
export type SignupErrors = Partial<Record<keyof SignupInput, string>>;
export type SignupValidation = { ok: true; value: SignupInput } | { ok: false; errors: SignupErrors };

export const NAME_MAX_LENGTH = 80;
const EMAIL_MAX_LENGTH = 254;
const DOMAIN_LABEL_MAX_LENGTH = 63;
const LOCAL_PART_PATTERN = /^[^\s@]+$/;
// Letters (including internationalised ones), digits and inner hyphens.
const DOMAIN_LABEL_PATTERN = /^[\p{L}\p{N}](?:[\p{L}\p{N}-]*[\p{L}\p{N}])?$/u;

/**
 * A deliberately simple structural check: one "@", a local part without leading, trailing or repeated dots, and a domain
 * of at least two non-empty labels. It rejects malformed domains such as "alice@.example.com" and "alice@example..com".
 */
export function isValidEmail(email: string): boolean {
    if (email.length > EMAIL_MAX_LENGTH) {
        return false;
    }
    const parts = email.split('@');
    if (parts.length !== 2) {
        return false;
    }
    const [local, domain] = parts as [string, string];
    if (!LOCAL_PART_PATTERN.test(local) || local.startsWith('.') || local.endsWith('.') || local.includes('..')) {
        return false;
    }
    const labels = domain.split('.');
    return (
        labels.length >= 2 &&
        labels.every((label) => label.length <= DOMAIN_LABEL_MAX_LENGTH && DOMAIN_LABEL_PATTERN.test(label))
    );
}

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
    } else if (!isValidEmail(email)) {
        errors.email = 'Enter a valid email address.';
    }

    return Object.keys(errors).length > 0 ? { ok: false, errors } : { ok: true, value: { name, email } };
}
