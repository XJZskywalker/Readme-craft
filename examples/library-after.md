# fastparse

Builds runtime validators from small schema objects, with TypeScript types inferred from the same declaration.

## Install

```bash
npm install fastparse
```

Ships as ESM and CommonJS. No runtime dependencies.

## Quick start

```ts
import { object, string, number, array } from "fastparse";

const User = object({
  id: number(),
  name: string(),
  tags: array(string()),
});

const user = User.check(payload);  // typed as { id: number; name: string; tags: string[] }
```

`check` throws on the first failure. `User.safeCheck(payload)` returns `{ ok: true, value }` or `{ ok: false, error }` instead.

## Errors

A failed check throws `ParseError` with the location of the failure:

```ts
ParseError: expected number at $.tags[2]
  received: "red"
```

`error.path` is a JSON Pointer, so it can be logged or mapped back to a form field.

## API

| Export | Signature | Notes |
|---|---|---|
| `object(shape)` | `Schema<T>` | Unknown keys are dropped unless `strict` is set |
| `string()` | `Schema<string>` | Options: `min`, `max`, `pattern` |
| `number()` | `Schema<number>` | Rejects `NaN` and `Infinity` |
| `array(item)` | `Schema<T[]>` | Empty arrays pass unless `min` is set |
| `optional(schema)` | `Schema<T \| undefined>` | Missing key only; `null` still fails |

`setMessage(schema, text)` overrides the default message for one schema node.

## Behaviour worth knowing

Validation is single-pass and allocation-light; a 1 MB nested payload validates in roughly 12 ms on a 2020 MacBook Air. On failure it stops at the first error rather than collecting all of them — if you need every error at once, call `safeCheck` per key.

Transforms run after validation, so a `coerce` option can convert `"12"` to `12` without weakening the check for other inputs.

## Compatibility

Node 18+, all modern browsers, and any bundler that resolves the `exports` field. Requires TypeScript 4.7+ for the type inference.

## License

MIT
