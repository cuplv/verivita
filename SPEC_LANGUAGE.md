# Description of the specification language

# Grammar
- Reserved keywords and operators:
Reserved keywords:
```
SPEC, TRUE, FALSE, CB, CI, #, NULL
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
       | (regexp)
```

The regular expressions are defined over Boolean expressions of
messages. In these settings, a `bexp` describes a set of possible
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
     | (bexp)
```

`bexp` defines the Boolean expressions where the atoms are messages.
The operators `!`, `&` and `|` are the standard Boolean negation,
conjunction and disjunction respectively.


- Message

A message represents a callin or a callback, it may predicates over
the return value of the callin or callback and have free variables for
the parameters.


```
message : param = [method_type] method_call
        | [method_type] method_call
        | TRUE
        | FALSE

method_type : CB
            | CI

method_call : [param] inner_call
            | inner_call
            
inner_call : composed_id composed_id(param_list)
           | composed_id composed_id()
           
param_list : param : composed_id
           | param : composed_id, param_list
           
param : identifier
      | TRUE
      | FALSE
      | NULL
      | integer
      | string_literal
      | #

composed_id : identifier
            | identifier.composed_id
            
identifier = [a-zA-Z_$][a-zA-Z0-9_$]*
integer = [1-9]*[0-9]+
string_literal = c-like string
```

A message can be either `TRUE`, `FALSE`, define a callin or a
callback.

`TRUE` specifies the set of all the possible messages, while `FALSE`
specifies the empty set of messages.

When the method call is prepended by `param = `, it means that the
rules applies to the method call that returns a value `param`.

*NOTE* the rule with `param =` will not match any method that do not
return any value (i.e. `void` return type), while the rule without
`param = ` will only match methods that do not return any value
(i.e. `void` return type).

The type of the method can either be `CI` or `CB`, specifiying that
the method is a callin or a callback.

`method_call` defines the call to a method.

The method call is defined by an optional receiver `[param]
inner_call` (the object used to invoke the method), 
a return type (a `composed_id`), the method name and a list of
parameters (`param_list`).

The name of the method is a `composed_id`, and specifies both the full
class name (with the package) and the method name, separated by dots.


The receiver is a `param` and the parameter list is either empty or a
comma separated list of parameters (`param`).
A parameter `param` can be a constant value, a free variable, or any
value, specifified with the reserved keyword `#`.

Each parameters in `param_list` must be followed by their type (the
one that corresponds to the types found in the method signature). The
type is a `composed_id`.


# Examples

For example, we want to specify that the
`android.widget.Button.setOnClickListener` callin called on a button
`b` and with a click listener instance `l` as parameter enables the
callback `onClick` called on the same listener `l` with the button `b`
as parameter.

This is achieved with the following specification:
```
SPEC [CI] [b] void android.widget.Button.setOnClickListener(l : View.OnClickListener) |+ [CB] [l] void onClick(b : android.widget.Button)
```

Note that the regular expression only matches an execution where the
*first* callin called is `setOnClickListener`.
To specify that, independently from the previous callins/callbacks,
when the method `setOnClickListener` is executed then `onClick` is
enabled, we have to match an unbounded number of letters before the
method:

```
SPEC TRUE[*]; [CI] [b] void android.widget.Button.setOnClickListener(l : View.OnClickListener) |+ [CB] [l] void onClick(b : android.widget.Button)
```

This specification tells that one can see any number of method calls
before the `setOnClickListener`.


# Hints

- Force an effect in the intial state of the system:
```
SPEC FALSE[*] |- [CI] [l] void callin(b : Button)
```

In this case the callin `void callin(b : Button)` will be disabled at
the beginning of the execution (note that `FALSE[*]` accepts only the
empty word).




