# Description of the specification language

# Grammar
- Reserved keywords and operators
Reserved keywords:
```
SPEC, TRUE, FALSE, CB, CI, #, NULL
```

- Operators
```
=, !, &, |, ;, [*], |-, |+
```

- Comments

All the symbols on a line that follows the sequence `//` are comments, and they will be ignored by the parser (i.e. like single line comments in C or Java).


- List of specifications
```
specs : spec
      | spec; specs
      | named_regexp
      | named_regexp; specs
```
The specification file contains a semicolon separated list of
specifications or named regular expressions

- Specification
```
spec : SPEC regexp |- message
     | SPEC regexp |+ message
     | SPEC regexp |- message ALIAS aliases
     | SPEC regexp |+ message ALIAS aliases
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
regexp : message
       | regexp[*]
       | regexp; regepx
       | regexp & regexp
       | regepx | regexp
       | ! regexp
       | (regexp)
```

The regular expressions are defined over messages.

`[*]` is the Kleene star  operator, `;` is the sequence, `|` is the
union, `&` intersection and `!` the complement.

*NOTE*: at the end we do not have Boolean expressions as in PSL, since
 the message is not really a Boolean variable. We really have regular
 expressions.
 
The optimization where we represent sets of transitions with multiple
labels symbolically is in the representation used to process the
specs (for example, we represents the set of all the transitions
different from `a` as `! a`, instead of enumerating them).


- Message

A message represents either the execution of the entry or exit of a callin or a callback.

A message is identified by the name of the method and its parameters.
In the case of an exit, it is also identified by the return value. All
the parameters and return values used in the specification may be
concrete values (e.g. 3 for an integer type paraemeter) or free
variables (e.g. x).


```
message : param = [method_type] [EXIT] method_call
        | [method_type] [ENTRY] method_call
        | [method_type] [EXIT] method_call
        | TRUE
        | FALSE

method_type : CB
            | CI
            
entry_type  : ENTRY
            | EXIT

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

A message can be either `TRUE`, `FALSE`, define a callin or a callback entry/exit.

`TRUE` specifies the set of all the possible messages, while `FALSE` specifies the empty set of messages.

When the method call is prepended by `param = `, it means that the
rules applies to the exit of a method call that returns a value `param`.

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


- Aliases
Aliases can be used to rename name of the method used in a message.

As an example, in the specification:
```
SPEC [CI] [ENTRY] [l] void method_name() |- TRUE ALIASES method_name = [subs1,subs2]
```
the alias tells to change all the messages that have `method_name` as method name with `subs1` and with `subs2`

This results in specifying two different specifications:
```
SPEC [CI] [ENTRY] [l] void subs1() |- TRUE
SPEC [CI] [ENTRY] [l] void subs2() |- TRUE
```

One can obtain all the possible substitutions defined by the aliases. For example:
```
SPEC [CI] [ENTRY] [l] void method_name() |- [CI] [ENTRY] [l] void method_name2() 
    ALIASES method_name = [subs1, subs2], method_name2 = [subs3, subs4]
```
Is expanded as 4 different specifications as:
```
SPEC [CI] [ENTRY] [l] void subs1() |- [CI] [ENTRY] [l] void subs3()
SPEC [CI] [ENTRY] [l] void subs1() |- [CI] [ENTRY] [l] void subs4()
SPEC [CI] [ENTRY] [l] void subs2() |- [CI] [ENTRY] [l] void subs3()
SPEC [CI] [ENTRY] [l] void subs2() |- [CI] [ENTRY] [l] void subs4()
```

```
aliases : composed_id = [alias_list]
        | composed_id = [alias_list], aliases
        
alias_list : composed_id
           | composed_id, alias_list
```

- Named regular expressions

The language allow to define templates for regular expressions that can be used in different places.

```
named_regexp : REGEXP id(var_list) = [regexp]
```
where `var_list` is a list of identifiers:
```
var_list : identifier
         | identifier, var_list
```

A named regular expression can be used in a spec or in another named regular expression (avoiding circular definitions).
The named regular expression is insereted by using its name and passing the correspondent parameters (e.g. they can be other variables or concrete values).

All the bounded variables of the regular expressions (i.e. the one that appear in the `var_list`) are substituted in a concrete instantiation of the named by name.

When substituting all the variables that are not bounded (free), we substitute them with a free variable that is not present in the containing expression to avoid variable capture.

For example we can define the `PRED1` regular expression and reuse it in a `SPEC` as follows:
```
NAMED_EXPR PRED1(l,v) = [[CB] [ENTRY] [l] void view.onClick(v : View)];
SPEC PRED(l,v); [CI] [ENTRY] [b] boolean view.setVisible(true) |- 
```

# Examples
For example, we want to specify that the
`android.widget.Button.setOnClickListener` callin called on a button
`b` and with a click listener instance `l` as parameter enables the
callback `onClick` called on the same listener `l` with the button `b`
as parameter.

This is achieved with the following specification:
```
SPEC [CI] [ENTRY] [b] void android.widget.Button.setOnClickListener(l : View.OnClickListener) |+ [CB] [ENTRY] [l] void onClick(b : android.widget.Button)
```

Note that the regular expression only matches an execution where the *first* callin called is `setOnClickListener`.
To specify that, independently from the previous callins/callbacks sequences,
when the method `setOnClickListener` is executed then `onClick` is enabled, we have to match an unbounded number of letters before the method:

```
SPEC TRUE[*]; [CI] [ENTRY] [b] void android.widget.Button.setOnClickListener(l : View.OnClickListener) |+ [CB] [ENTRY] [l] void onClick(b : android.widget.Button)
```

This specification tells that one can see any number of method calls before the `setOnClickListener`.


# Hints

- To force an effect in the intial state of the system one can use the `FALSE[*]` expression:
```
SPEC FALSE[*] |- [CI] [ENTRY] [l] void callin(b : Button)
```

In this case the callin `void callin(b : Button)` will be disabled at the beginning of the execution (note that `FALSE[*]` accepts only the empty word).




