module QueryTrace exposing (..)

-- DO NOT EDIT
-- AUTOGENERATED BY THE ELM PROTOCOL BUFFER COMPILER
-- https://github.com/tiziano88/elm-protobuf
-- source file: QueryTrace.proto

import Protobuf exposing (..)

import Json.Decode as JD
import Json.Encode as JE


type alias CTrace =
    { id : Maybe TraceIdentifier -- 1
    , callbacks : List CallbackOrHole -- 2
    }


cTraceDecoder : JD.Decoder CTrace
cTraceDecoder =
    JD.lazy <| \_ -> decode CTrace
        |> optional "id" traceIdentifierDecoder
        |> repeated "callbacks" callbackOrHoleDecoder


cTraceEncoder : CTrace -> JE.Value
cTraceEncoder v =
    JE.object <| List.filterMap identity <|
        [ (optionalEncoder "id" traceIdentifierEncoder v.id)
        , (repeatedFieldEncoder "callbacks" callbackOrHoleEncoder v.callbacks)
        ]


type alias TraceIdentifier =
    { appName : String -- 1
    , gitRepo : String -- 2
    , traceName : String -- 3
    }


traceIdentifierDecoder : JD.Decoder TraceIdentifier
traceIdentifierDecoder =
    JD.lazy <| \_ -> decode TraceIdentifier
        |> required "appName" JD.string ""
        |> required "gitRepo" JD.string ""
        |> required "traceName" JD.string ""


traceIdentifierEncoder : TraceIdentifier -> JE.Value
traceIdentifierEncoder v =
    JE.object <| List.filterMap identity <|
        [ (requiredFieldEncoder "appName" JE.string "" v.appName)
        , (requiredFieldEncoder "gitRepo" JE.string "" v.gitRepo)
        , (requiredFieldEncoder "traceName" JE.string "" v.traceName)
        ]


type alias CallbackOrHole =
    { cbCommand : CbCommand
    }


type CbCommand
    = CbCommandUnspecified
    | Callback CCallback
    | CbHole Hole


cbCommandDecoder : JD.Decoder CbCommand
cbCommandDecoder =
    JD.lazy <| \_ -> JD.oneOf
        [ JD.map Callback (JD.field "callback" cCallbackDecoder)
        , JD.map CbHole (JD.field "cbHole" holeDecoder)
        , JD.succeed CbCommandUnspecified
        ]


cbCommandEncoder : CbCommand -> Maybe ( String, JE.Value )
cbCommandEncoder v =
    case v of
        CbCommandUnspecified ->
            Nothing
        Callback x ->
            Just ( "callback", cCallbackEncoder x )
        CbHole x ->
            Just ( "cbHole", holeEncoder x )


callbackOrHoleDecoder : JD.Decoder CallbackOrHole
callbackOrHoleDecoder =
    JD.lazy <| \_ -> decode CallbackOrHole
        |> field cbCommandDecoder


callbackOrHoleEncoder : CallbackOrHole -> JE.Value
callbackOrHoleEncoder v =
    JE.object <| List.filterMap identity <|
        [ (cbCommandEncoder v.cbCommand)
        ]


type alias CCallback =
    { methodSignature : String -- 1
    , firstFrameworkOverrrideClass : String -- 2
    , applicationClass : String -- 3
    , parameters : List CParam -- 4
    , receiver : Maybe CParam -- 5
    , returnValue : Maybe CParam -- 6
    , exception : Maybe CException -- 7
    , nestedCommands : List CCommand -- 8
    }


cCallbackDecoder : JD.Decoder CCallback
cCallbackDecoder =
    JD.lazy <| \_ -> decode CCallback
        |> required "methodSignature" JD.string ""
        |> required "firstFrameworkOverrrideClass" JD.string ""
        |> required "applicationClass" JD.string ""
        |> repeated "parameters" cParamDecoder
        |> optional "receiver" cParamDecoder
        |> optional "returnValue" cParamDecoder
        |> optional "exception" cExceptionDecoder
        |> repeated "nestedCommands" cCommandDecoder


cCallbackEncoder : CCallback -> JE.Value
cCallbackEncoder v =
    JE.object <| List.filterMap identity <|
        [ (requiredFieldEncoder "methodSignature" JE.string "" v.methodSignature)
        , (requiredFieldEncoder "firstFrameworkOverrrideClass" JE.string "" v.firstFrameworkOverrrideClass)
        , (requiredFieldEncoder "applicationClass" JE.string "" v.applicationClass)
        , (repeatedFieldEncoder "parameters" cParamEncoder v.parameters)
        , (optionalEncoder "receiver" cParamEncoder v.receiver)
        , (optionalEncoder "returnValue" cParamEncoder v.returnValue)
        , (optionalEncoder "exception" cExceptionEncoder v.exception)
        , (repeatedFieldEncoder "nestedCommands" cCommandEncoder v.nestedCommands)
        ]


type alias CCommand =
    { ciCommand : CiCommand
    }


type CiCommand
    = CiCommandUnspecified
    | Callin CCallin
    | CiHole Hole


ciCommandDecoder : JD.Decoder CiCommand
ciCommandDecoder =
    JD.lazy <| \_ -> JD.oneOf
        [ JD.map Callin (JD.field "callin" cCallinDecoder)
        , JD.map CiHole (JD.field "ciHole" holeDecoder)
        , JD.succeed CiCommandUnspecified
        ]


ciCommandEncoder : CiCommand -> Maybe ( String, JE.Value )
ciCommandEncoder v =
    case v of
        CiCommandUnspecified ->
            Nothing
        Callin x ->
            Just ( "callin", cCallinEncoder x )
        CiHole x ->
            Just ( "ciHole", holeEncoder x )


cCommandDecoder : JD.Decoder CCommand
cCommandDecoder =
    JD.lazy <| \_ -> decode CCommand
        |> field ciCommandDecoder


cCommandEncoder : CCommand -> JE.Value
cCommandEncoder v =
    JE.object <| List.filterMap identity <|
        [ (ciCommandEncoder v.ciCommand)
        ]


type alias Hole =
    { isSelected : Bool -- 1
    }


holeDecoder : JD.Decoder Hole
holeDecoder =
    JD.lazy <| \_ -> decode Hole
        |> required "isSelected" JD.bool False


holeEncoder : Hole -> JE.Value
holeEncoder v =
    JE.object <| List.filterMap identity <|
        [ (requiredFieldEncoder "isSelected" JE.bool False v.isSelected)
        ]


type alias CCallin =
    { methodSignature : String -- 1
    , frameworkClass : String -- 2
    , parameters : List CParam -- 3
    , receiver : Maybe CParam -- 4
    , returnValue : Maybe CParam -- 5
    , exception : Maybe CException -- 6
    , nestedCallbacks : List CCallback -- 8
    }


cCallinDecoder : JD.Decoder CCallin
cCallinDecoder =
    JD.lazy <| \_ -> decode CCallin
        |> required "methodSignature" JD.string ""
        |> required "frameworkClass" JD.string ""
        |> repeated "parameters" cParamDecoder
        |> optional "receiver" cParamDecoder
        |> optional "returnValue" cParamDecoder
        |> optional "exception" cExceptionDecoder
        |> repeated "nestedCallbacks" cCallbackDecoder


cCallinEncoder : CCallin -> JE.Value
cCallinEncoder v =
    JE.object <| List.filterMap identity <|
        [ (requiredFieldEncoder "methodSignature" JE.string "" v.methodSignature)
        , (requiredFieldEncoder "frameworkClass" JE.string "" v.frameworkClass)
        , (repeatedFieldEncoder "parameters" cParamEncoder v.parameters)
        , (optionalEncoder "receiver" cParamEncoder v.receiver)
        , (optionalEncoder "returnValue" cParamEncoder v.returnValue)
        , (optionalEncoder "exception" cExceptionEncoder v.exception)
        , (repeatedFieldEncoder "nestedCallbacks" cCallbackEncoder v.nestedCallbacks)
        ]


type alias CParam =
    { param : Param
    }


type Param
    = ParamUnspecified
    | Variable CVariable
    | Primitive CPrimitive
    | Object CObject
    | PrHole Hole


paramDecoder : JD.Decoder Param
paramDecoder =
    JD.lazy <| \_ -> JD.oneOf
        [ JD.map Variable (JD.field "variable" cVariableDecoder)
        , JD.map Primitive (JD.field "primitive" cPrimitiveDecoder)
        , JD.map Object (JD.field "object" cObjectDecoder)
        , JD.map PrHole (JD.field "prHole" holeDecoder)
        , JD.succeed ParamUnspecified
        ]


paramEncoder : Param -> Maybe ( String, JE.Value )
paramEncoder v =
    case v of
        ParamUnspecified ->
            Nothing
        Variable x ->
            Just ( "variable", cVariableEncoder x )
        Primitive x ->
            Just ( "primitive", cPrimitiveEncoder x )
        Object x ->
            Just ( "object", cObjectEncoder x )
        PrHole x ->
            Just ( "prHole", holeEncoder x )


cParamDecoder : JD.Decoder CParam
cParamDecoder =
    JD.lazy <| \_ -> decode CParam
        |> field paramDecoder


cParamEncoder : CParam -> JE.Value
cParamEncoder v =
    JE.object <| List.filterMap identity <|
        [ (paramEncoder v.param)
        ]


type alias CVariable =
    { name : String -- 1
    }


cVariableDecoder : JD.Decoder CVariable
cVariableDecoder =
    JD.lazy <| \_ -> decode CVariable
        |> required "name" JD.string ""


cVariableEncoder : CVariable -> JE.Value
cVariableEncoder v =
    JE.object <| List.filterMap identity <|
        [ (requiredFieldEncoder "name" JE.string "" v.name)
        ]


type alias CObject =
    { id : Int -- 1
    }


cObjectDecoder : JD.Decoder CObject
cObjectDecoder =
    JD.lazy <| \_ -> decode CObject
        |> required "id" intDecoder 0


cObjectEncoder : CObject -> JE.Value
cObjectEncoder v =
    JE.object <| List.filterMap identity <|
        [ (requiredFieldEncoder "id" numericStringEncoder 0 v.id)
        ]


type alias CPrimitive =
    { primitive : Primitive
    }


type Primitive
    = PrimitiveUnspecified
    | IntVal Int
    | LongVal Int
    | StringVal String
    | BoolVal Bool


primitiveDecoder : JD.Decoder Primitive
primitiveDecoder =
    JD.lazy <| \_ -> JD.oneOf
        [ JD.map IntVal (JD.field "intVal" intDecoder)
        , JD.map LongVal (JD.field "longVal" intDecoder)
        , JD.map StringVal (JD.field "stringVal" JD.string)
        , JD.map BoolVal (JD.field "boolVal" JD.bool)
        , JD.succeed PrimitiveUnspecified
        ]


primitiveEncoder : Primitive -> Maybe ( String, JE.Value )
primitiveEncoder v =
    case v of
        PrimitiveUnspecified ->
            Nothing
        IntVal x ->
            Just ( "intVal", JE.int x )
        LongVal x ->
            Just ( "longVal", numericStringEncoder x )
        StringVal x ->
            Just ( "stringVal", JE.string x )
        BoolVal x ->
            Just ( "boolVal", JE.bool x )


cPrimitiveDecoder : JD.Decoder CPrimitive
cPrimitiveDecoder =
    JD.lazy <| \_ -> decode CPrimitive
        |> field primitiveDecoder


cPrimitiveEncoder : CPrimitive -> JE.Value
cPrimitiveEncoder v =
    JE.object <| List.filterMap identity <|
        [ (primitiveEncoder v.primitive)
        ]


type alias CException =
    {
    }


cExceptionDecoder : JD.Decoder CException
cExceptionDecoder =
    JD.lazy <| \_ -> decode CException


cExceptionEncoder : CException -> JE.Value
cExceptionEncoder v =
    JE.object <| List.filterMap identity <|
        [
        ]


type alias CMessage =
    { msg : Msg
    }


type Msg
    = MsgUnspecified
    | MCallin CCallin
    | MCallback CCallback
    | MProblem CProblem


msgDecoder : JD.Decoder Msg
msgDecoder =
    JD.lazy <| \_ -> JD.oneOf
        [ JD.map MCallin (JD.field "mCallin" cCallinDecoder)
        , JD.map MCallback (JD.field "mCallback" cCallbackDecoder)
        , JD.map MProblem (JD.field "mProblem" cProblemDecoder)
        , JD.succeed MsgUnspecified
        ]


msgEncoder : Msg -> Maybe ( String, JE.Value )
msgEncoder v =
    case v of
        MsgUnspecified ->
            Nothing
        MCallin x ->
            Just ( "mCallin", cCallinEncoder x )
        MCallback x ->
            Just ( "mCallback", cCallbackEncoder x )
        MProblem x ->
            Just ( "mProblem", cProblemEncoder x )


cMessageDecoder : JD.Decoder CMessage
cMessageDecoder =
    JD.lazy <| \_ -> decode CMessage
        |> field msgDecoder


cMessageEncoder : CMessage -> JE.Value
cMessageEncoder v =
    JE.object <| List.filterMap identity <|
        [ (msgEncoder v.msg)
        ]


type alias CMessageList =
    { msgs : List CMessage -- 1
    }


cMessageListDecoder : JD.Decoder CMessageList
cMessageListDecoder =
    JD.lazy <| \_ -> decode CMessageList
        |> repeated "msgs" cMessageDecoder


cMessageListEncoder : CMessageList -> JE.Value
cMessageListEncoder v =
    JE.object <| List.filterMap identity <|
        [ (repeatedFieldEncoder "msgs" cMessageEncoder v.msgs)
        ]


type alias CProblem =
    { description : String -- 1
    }


cProblemDecoder : JD.Decoder CProblem
cProblemDecoder =
    JD.lazy <| \_ -> decode CProblem
        |> required "description" JD.string ""


cProblemEncoder : CProblem -> JE.Value
cProblemEncoder v =
    JE.object <| List.filterMap identity <|
        [ (requiredFieldEncoder "description" JE.string "" v.description)
        ]


type alias VerificationResult =
    { msg : String -- 1
    , counterExample : Maybe CTrace -- 2
    , status : String -- 3
    }


verificationResultDecoder : JD.Decoder VerificationResult
verificationResultDecoder =
    JD.lazy <| \_ -> decode VerificationResult
        |> required "msg" JD.string ""
        |> optional "counterExample" cTraceDecoder
        |> required "status" JD.string ""


verificationResultEncoder : VerificationResult -> JE.Value
verificationResultEncoder v =
    JE.object <| List.filterMap identity <|
        [ (requiredFieldEncoder "msg" JE.string "" v.msg)
        , (optionalEncoder "counterExample" cTraceEncoder v.counterExample)
        , (requiredFieldEncoder "status" JE.string "" v.status)
        ]