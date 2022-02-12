## 0.5.0
- Stringify `Expression` objects reasonably
  ```
  f.a -> "f.a"
  f['a'] -> "f[a]"
  mean(f.a) -> "mean(f.a)"
  f.a + 1 -> "f.a + 1"
  ```
- Deprecate `DirectRefAttr` and `DirectRefItem`. Use `ref._pipda_level` instead.
  ```
  f -> f._pipda_level == 0
  f.a -> f._pipda_level == 1
  f.a.b -> f._pipda_level == 2
  ```
- Household
  Use `flake8` instead of `pylint` for linting.

## 0.4.5
- Add `CallingEnvs.REGULAR`

## 0.4.4
- Add `options` and `options_context`.
- Move `warn_astnode_failure` to options
- Add `assume_all_piping` mode

## 0.4.3
- Avoid raising exception for `varname()` to get the name of `Symbolic` object.

## 0.4.2
- Make Function property private thus accessiable to `getattr()` (otherwise returns an `Expression` object)
- Give better repr for Function when func is an Expression object.

## 0.4.1
- Fix `getattr()` failure for operator-connected expressions (pwwang/datar#38)

## 0.4.0
- Improve calling rules for verbs, data functions and non-data functions
- Remove `evaluate_args()` and `evaluate_kwargs()`, use `evaluate_expr()` instead

## 0.3.0
Added:
- Add a better regular calling strategy and warn for ambiguity
- Support #11

Breaking changes:
- Rename `register_piping_sign` to `register_piping`

## 0.2.9
- Avoid func of Function object to be re-evaluated (fixing datar#14)

## 0.2.8
- Add `is_direct` argument to context getitem/getattr to tell if the reference is a direct reference.

## 0.2.7
- Allow `Reference objects` to be functions (callable)

## 0.2.6
- Let `Symbolic.__getitem__` return `DirectRefItem` instead of `ReferenceItem`

## 0.2.5
- Allow custom evaluation for objects in verb arguments.

## 0.2.4
- Allow extra attributes to be registered together with funcs/verbs

## 0.1.6
- Allow to register different context for different types
- Allow verb to be used as argument of a verb
