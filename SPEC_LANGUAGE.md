# Description of the specification language

# Grammar
- Reserved keywords and operators:
Reserved keywords:
```
SPEC, TRUE, FALSE, CB, CI, #
```

Operators:
```
=, !, &, |, ;, [*], |-, |+,
```

- List of specifications
```
specs : spec
      | spec; specs
```
The specification file contains a semicolon separated list of
specifications.

- Specification
```
spec : SPEC regexp |- message
     | SPEC regexp |+ message
```

A specification is formed by a regular expression `regexp`, the
operator of the specification (`|-` or `|+`) and a message affected by
the specification `message`.

`regexp` is a regular expression over messages.

The specification applies the operator to the message as soon as the
execution is matched by the regular expression (is a word in the
language defined by the regexp).

The operator `|-` disables/disallow `message`, while `|+`
enable/allow `message`.


- Regular expressions
```
regexp : bexp
       | bexp[*]
       | regexp; regepx
```

The regular expressions are defined over Boolean expressions of
messages. In these settings, a `bexp` describe a set of possible
messages.

`[*]` is the Kleene star operator that can be applied only to a
`bexp`, a Boolean combination of messages.
The `;` operator is the concatenation operator.


- Boolean expressions
```
bexp : message
     | ! bexp
     | bexp & bexp
     | bexp | bexp
```

`bexp` defines the Boolean expressions where the atoms are messages.
The operators `!`, `&` and `|` are the standard Boolean negation,
conjunction and disjunction respectively.


- Message

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
            
identifier = [a-zA-Z_$][a-zA-Z0-9_$]*
integer = [1-9]*[0-9]+

```

A message can be either `TRUE`, `FALSE`, define a callin or a
callback.

`TRUE` specifies the set of all the possible messages, while `FALSE`
specifies the empty set of messages.

When the method call is prepended by `freevar = `, it means that the
rules applies to the method call that returns `freevar`.

The type of the method can either be `CI` or `CB`, specifiying that
the method is a callin or a callback.

`method_call` defines the call to a method.

The name of the method is a `composed_id`, and specifies both the
full class name (with the package) and the method name, separated by
dots.

The method call may specify a receiver (`[freevar] inner_call`) or
not and a list of parameters.

The parameters can be constant values, free variables, or any value,
specifified with the reserved keyword `#`.


# Examples

For example, we want to specify that the
`android.widget.Button.setOnClickListener` callin called on a button
`b` and with a click listener instance `l` as parameter enables the
callback `onClick` called on the same listener `l` with the button `b`
as parameter.

This is achieved with the following specification:
```
SPEC [CI] [b] android.widget.Button.setOnClickListener(l) |+ [CB] [l] onClick(b)
```

Note that the regular expression only matches an execution where the
*first* callin called is `setOnClickListener`.
To specify that, independetly from the previous callins/callbacks,
when the method `setOnClickListener` is executed then `onClick` is
enabled, we have to match an unbounded number of letters before the
method:

```
SPEC TRUE[*]; [CI] [b] android.widget.Button.setOnClickListener(l) |+ [CB] [l] onClick(b)
```

This specification tells that one can see any number of method calls
before the `setOnClickListener`.





