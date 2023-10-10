# Change Log

## 0.13.1

- ✨ Add `__array_function__` to `Expression` objects

## 0.13.0

- ✨ Add Dockerfile for codesandbox
- ⬆️ Bump executing to `^2.0`
- ✨ Support python 3.12

## 0.12.0

- ⬆️ Drop support for python3.7

## 0.11.1

- 👷 Use newer actions
- 📝 Fix github action badegs
- 🩹 Allow ast_fallback to be changed for verbs and functions

## 0.11.0

- 💥 Simplify `register_expr_array_func` and rename it to `register_array_ufunc`

## 0.10.0

- 💥 Refactor the registered borrowed from `singledispatch`
- ✨ Allow pipeable and dispatchable functions (related: pwwang/datar#148)
- 💥 Change default ast_fallback to "piping_warning" for verbs
- ✨ Allow to register multi-types at a time for dispatchable functions
- ✨ Support backends
- ✨ Allow register plain functions
- ✅ Add level test for context
- ✨ Make pipeable function work as a verb

## 0.9.0

- ✨ Allow `__array_ufunc__` to be registered on Expression by `register_expr_array_func`

## 0.8.2

- ✨ Support other numpy ufunc methods

## 0.8.1

- ✨ Allow verb to be a placeholder (without any types registered)
- ✅ Add test for npufuncs to be used in verbs

## 0.8.0

- patch classes if they have piping operator method
- auto register numpy ufuncs
- pump executing to 1.1.1 to fix pwwang/datar#149

## 0.7.6

- 🐛 Fix `numpy.ndarray` as data argument for verbs
- 🚚 Rename `Expression.operator` to `Expression._pipda_operator`

## 0.7.5

- ✨ Allow function meta infor to be overwritten

## 0.7.4

- 🐛 Allow numpy.ufuncs to be registered

## 0.7.3

- ✨ Make `register` an alias of `register_verb`

## 0.7.2

- ✨ Allow registering generic verbs

## 0.7.1

- 🐛 Fix VerbCall `__str__`
- ⚡️ Make Symbolic a singleton
- 🐛 Allow general keyword arg for extra contexts
- 🧱 Always enable `ast_fallback_arg`
- 💥 Change the way verbs used as funcs
- 🩹 Allow func passed directly to register_verb

## 0.7.0

- ♻️ Refactor to decrease complexity

## 0.6.0

- 📌 Pin versions of dependencies

## 0.5.9

- 🚑 Fix ImproperUseError of varname for Symbolic
- 📝 Pin deps for docs

## 0.5.8

- 🐛 Fix `f >> verb(...)` as argument of another verb in assume_all_piping mode

## 0.5.7

- 🐛 Fix `f.x.mean()` evaluation in all-piping mode

## 0.5.6

- 🚑 Fix context meta not recovered when error

## 0.5.5

- 🚑 Fix stringify slice when it appears as ref of a `ReferenceItem` object

## 0.5.4

- ✨ Add `with_meta()` for context to evaluate expr temporarily

## 0.5.3

- 🚑 Fix operator func lookup for `Operator`
- 🩹 Don't stringify the Symbolic object

  ```python
  f.a
  # previously: "f.a", now: "a"
  f['a']
  # previously: "f[a]", now: "a"
  f.a['b']
  # previously: "f.a[b]", now: "a[b]"
  mean(f.a)
  # previously: "mean(f.a)", now: "mean(a)"
  f.a + 1
  # previously: "f.a + 1", now: "a + 1"
  ```

## 0.5.2

- Add `level` argument to context.getitem()/getattr() so that the expression level can be used in evaluation;
- Add `eval_symbolic()` to context to allow evaluate Symbolic objects in different ways.

## 0.5.1

- Remove abstract property `name` from contexts (`name` is no longer a required property to subclass `ContextBase`)
- Allow meta data of context to be passed down

  ```python
  from pipda import Symbolic, register_func, register_verb, evaluate_expr
  from pipda.context import Context, ContextEval

  f = Symbolic()

  @register_func(None, context=Context.SELECT)
  def wrapper(x):
    return x

  @register_func(None, context=Context.EVAL)
  def times_meta(x, _context=None):
    return x * _context.meta["val"]

  @register_verb(dict, context=ContextEval({"val": 10}))
  def add(x, y):
    return x["a"] + y

  # metadata passed down to times_meta
  {"a": 1} >> add(wrapper(use_meta(f["a"])))
  # 12
  ```

## 0.5.0

- Stringify `Expression` objects reasonably

  ```python
  f.a -> "f.a"
  f['a'] -> "f[a]"
  mean(f.a) -> "mean(f.a)"
  f.a + 1 -> "f.a + 1"
  ```

- Deprecate `DirectRefAttr` and `DirectRefItem`. Use `ref._pipda_level` instead.

  ```python
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
