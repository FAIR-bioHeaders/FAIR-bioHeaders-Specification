// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. https://mozilla.org/MPL/2.0/.
// Preserve unbounded integer tokens before JSON.parse's Number rounding occurs.
export function parseExactJson(text) {
  return JSON.parse(text, (key, value, context) => {
    if (typeof value !== 'number') return value;
    if (!context || typeof context.source !== 'string') {
      throw Error('lossless integer parsing requires JSON reviver source support');
    }
    return /^-?(?:0|[1-9][0-9]*)$/.test(context.source) ? BigInt(context.source) : value;
  });
}

export function exactStringify(value) {
  const typed = item => {
    if (item === null) return ['null'];
    if (typeof item === 'bigint') return ['integer', item.toString()];
    if (typeof item === 'string') return ['string', item];
    if (typeof item === 'boolean') return ['boolean', item];
    if (typeof item === 'number') {
      if (!Number.isFinite(item)) throw Error('nonfinite JSON number');
      return ['number', Object.is(item, -0) ? '-0' : item.toString()];
    }
    if (Array.isArray(item)) return ['array', item.map(typed)];
    if (typeof item === 'object') return ['object', Object.entries(item).map(
      ([key, child]) => [key, typed(child)])];
    throw Error('unsupported JSON value');
  };
  return JSON.stringify(typed(value));
}
