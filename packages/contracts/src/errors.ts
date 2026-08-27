/**
 * Contract validation errors.
 *
 * One error type, carrying the field path and the reason. A contract violation
 * is a bug at a boundary, not a user error, so the message is written for
 * whoever has to fix it.
 */

export class ContractError extends Error {
  readonly field: string;
  readonly reason: string;

  constructor(field: string, reason: string) {
    super(`${field}: ${reason}`);
    this.name = "ContractError";
    this.field = field;
    this.reason = reason;
  }
}
