module ServerCounter exposing (..)

import Html exposing (..)
import Html.Events exposing (onClick)
import Http
import Json.Decode as Json
import Dict as Dict exposing (Dict)
import Html.Events exposing (onInput)


main : Program Never Model Msg
main =
    program
        { init = init
        , view = view
        , update = update
        , subscriptions = subscriptions
        }



-- MODEL


type alias Model =
    { counter : List Int
    , error : Maybe String
    , trace : Maybe Trace
    , traceChoice: List String
    , selection : Maybe String
    }


init : ( Model, Cmd Msg )
init =
    ( Model [] Nothing Nothing [] Nothing, getTraceList)



-- UPDATE

type alias TraceMsg = Dict String String
type alias Trace = List TraceMsg
type alias TraceList = List String
type Msg
    = IncrementServerCounter
    | ServerCounterUpdated (Result Http.Error Int)
    | GetTrace String
    | ResponseTrace (Result Http.Error Trace)
    | ResponseTraceList (Result Http.Error (List String))
    | VerifyTrace (Maybe String) String
    | ResponseVerification (Result Http.Error Trace)
    | ChangeSelection String


update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        IncrementServerCounter ->
            ( model, incrementCounterServer )

        ServerCounterUpdated (Ok newCounter) ->
            ( { model | counter = newCounter::model.counter, error = Nothing }, Cmd.none )

        ServerCounterUpdated (Err newError) ->
            ( { model | error = Just <| toString newError }, Cmd.none )
        ResponseTrace (Ok newTrace) ->
            ( { model | trace = Just newTrace}, Cmd.none)
        ResponseTrace (Err newError) ->
            ( {model | error = Just <| toString newError}, Cmd.none)
        GetTrace id -> (model, getTrace id)
        VerifyTrace (Just id) dis -> (model, verifyTrace id dis)
        VerifyTrace Nothing dis -> (model, Cmd.none)
        ResponseTraceList (Err newError) -> ( {model | error = Just <| toString newError}, Cmd.none)
        ResponseTraceList (Ok traceList) -> ( {model | traceChoice = traceList}, Cmd.none)
        ResponseVerification (Err newError) -> ( {model | error = Just <| toString newError}, Cmd.none)
        ResponseVerification (Ok newTrace) -> ( {model | trace = Just newTrace}, Cmd.none)
        ChangeSelection sel -> ({model | selection = Just sel}, Cmd.none)


-- VIEW


view : Model -> Html Msg
view model =
    div []
        [ --button [ onClick IncrementServerCounter ] [ text "Increment Server" ]
        --(List.range 0 (List.length model.traceChoice))
        --model.traceChoice
         select [onInput ChangeSelection] ( model.traceChoice
            |> (List.map text)
            |> (List.map (\a -> option [] [ a]))
            )
        , div [] [button [ onClick (GetTrace (Maybe.withDefault "" model.selection)) ] [ text "Get Trace" ]]
        , div [] [button [ onClick (VerifyTrace model.selection "1")] [ text "Verify Trace" ]]
--        , div [] (List.map (\ c -> (div [] [ text (toString c)])) model.counter)
        , (viewTrace (Maybe.withDefault [] model.trace))
        , div [] [ text (Maybe.withDefault "" model.error) ]
        ]

getND : String -> (Dict String String) -> String
getND key dict = Maybe.withDefault "" (Dict.get key dict)


viewTrace : Trace -> Html Msg
viewTrace trace = div [] (List.map viewMsg trace)


viewMsg : TraceMsg -> Html Msg
viewMsg traceMsg =
    let d = getND "directionIdent" traceMsg in
    let o = getND "opDescriptor" traceMsg in
    let r = getND "stackDescriptor" traceMsg in

    div [] [text (d ++ " " ++ r ++ " " ++ o)]


-- SUBSCRIPTIONS


subscriptions : Model -> Sub Msg
subscriptions model =
    Sub.none



-- HTTP


incrementCounterServer : Cmd Msg
incrementCounterServer =
    Http.send ServerCounterUpdated (Http.get "/count" decodeCounter)

getTrace : String -> Cmd Msg
getTrace id =
    Http.send ResponseTrace (Http.get ("/trace?traceId=" ++ id) decodeTrace)

verifyTrace : String -> String -> Cmd Msg
verifyTrace id did =
    Http.send ResponseVerification (Http.get ("/cxe?traceId=" ++ id ++ "&disallowId=" ++ did) decodeTrace)


getTraceList : Cmd Msg
getTraceList =
    Http.send ResponseTraceList (Http.get ("/tracelist") decodeTraceList)


decodeCounter : Json.Decoder Int
decodeCounter =
    Json.at [ "counter" ] Json.int

decodeTrace : Json.Decoder Trace
decodeTrace =
    Json.list (Json.dict Json.string)

decodeTraceList : Json.Decoder TraceList
decodeTraceList =
    Json.list Json.string