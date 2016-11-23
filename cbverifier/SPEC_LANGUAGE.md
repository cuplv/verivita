# Description of the specification language




# Grammar

- identifier:
```
identifier = [a-zA-Z_$][a-zA-Z0-9_$]*
```

- Reserved keywords:
```
SPEC, TRUE, FALSE, CB, CI, #
```

- Reverved operators:
```
=, !, &, |, ;, [*], |-, |+,
```

- List of specifications
```
specs : spec
      | spec; specs
```

- Specifications
```
spec : SPEC regexp |- message
     | SPEC regexp |+ message
```

The operator `|-` disables `message`, while `|+` enables message.
`regexp` is a regular expression over messages.


- Regular expressions (`regexp`)
```
regexp : bexp
       | bexp[*]
       | regexp; regepx
```

`[*]` is the Kleene star operator, which cna be applied only to a
`bexp`, a Boolean combination of messages.
The `;` operator is the concatenation operator.


- Boolean expressions (`bexp`)
```
bexp : message
     | ! bexp
     | bexp & bexp
     | bexp | bexp
```

The operators `!`, `&` and `|` are the Boolean negation, conjunction
and disjunction respectively.


- Messages (`message`)

A message represents a callin or a callback, it may predicates over
the return value of the callin or callback and have free variables for
the parameters.


```
message : freevar = [method_type] method_call
        | [method_type] method_call
        | TRUE
        | FALSE

method_type : CB
            | CI

freevar : identifier
        | #
        
method_call : [freevar] inner_call
            | inner_call
            
inner_call : composed_id(param_list)
           | composed_id()
           
param_list : param
           | param, param_list
           
param : identifier
      | TRUE
      | FALSE
      | integer
      | #

composed_id : identifier
            | identifier.composed_id

```
