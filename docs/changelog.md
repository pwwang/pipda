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
