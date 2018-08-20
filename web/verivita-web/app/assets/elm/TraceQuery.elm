module TraceQuery exposing (..)

import Html exposing (..)
--import Html.Events exposing (onClick)
import Http
--import Json.Decode as Json
import Json.Encode as Encode
import Bootstrap.CDN as CDN
import Bootstrap.Grid as Grid
import Bootstrap.Card as Card
import Html.Attributes exposing (class, src, style)
import Bootstrap.Card.Block as Block
import Bootstrap.Button as Button
--import Bootstrap.ListGroup as ListGroup
import Bootstrap.Form.Input as Input
import Bootstrap.Form.Checkbox as Checkbox
--import Json.Encode exposing (Value)
import QueryTrace as Qt


main : Program Never Model Msg
main =
    program
        {init = init
        , view = view
        , update = update
        , subscriptions = subscriptions}

-- Model

type Param -- note selected hole removed since query will be by clicking on a hole
    = NamedVar(String)
    | Hole


type QueryCallbackOrHole = QueryCallback(QueryCallbackData)
    | QueryCallbackHole
    | QueryCallbackHoleResults(List QueryCallbackData)
type alias QueryCallbackData =
    {
        frameworkClass : String,
        signature : String,
        input : String, -- Nothing when parsed successfully Just "" initially
        parsed : Bool,
        receiver : Param,
        commands : List QueryCommand,
        params : List Param,
        return : Param
    }

type QueryCommand
    = QueryCallin(QueryCallinData)
    | QueryCommandHole
type alias QueryCallinData =
    {
        frameworkClass: String,
        signature : String,
        input : String, -- Nothing when parsed successfully Just "" initially
        parsed : Bool,
        receiver : Param,
        return : Param,
        params : List Param
    }



type TraceValue
    = Null
    | Object(Int)
    | Integer(Int)
    | String(String) -- TODO: finish data types for concrete trace later
type alias TraceCallback =
    {
        frameworkClass : Maybe String,
        signature : Maybe String
    }

type alias Model =
    {
        query : List QueryCallbackOrHole
    }

emptyCallback : QueryCallbackOrHole
emptyCallback =
    QueryCallback( { frameworkClass = ""
        , signature = ""
        , receiver = Hole
        , return = Hole, commands = [], input="", parsed = False, params = []})

emptyCallin : QueryCommand
emptyCallin =
    QueryCallin({ frameworkClass = ""
        , signature = ""
        , receiver = Hole , return = Hole, input="", parsed = False, params = []})

init : ( Model, Cmd Msg)
init =
    ( Model [QueryCallbackHole], Cmd.none)


-- UPDATE

iAddCallin : List QueryCommand -> Int -> List QueryCommand
iAddCallin old cipos =
    case (old,cipos) of
        (t, -1) -> QueryCommandHole :: t
        (h :: t , 0) -> h :: QueryCommandHole :: t
        (nil , 0) -> QueryCommandHole :: nil
        (h :: t, a) -> h :: (iAddCallin t (a - 1))
        (nil , a) -> nil

iRemoveCallin : List a -> Int -> List a
iRemoveCallin old cipos =
    case (old,cipos) of
        (h :: t, 0) -> t
        (h :: t, a) -> h :: (iRemoveCallin t (cipos - 1))
        (nil,a) -> nil

iFill : List QueryCommand -> Int -> List QueryCommand
iFill old cipos =
    case (old,cipos) of
        (h :: t, 0) -> emptyCallin :: t
        (h :: t, a) -> h :: iFill t (a - 1)
        (nil,a) -> nil


doCallin
    : List QueryCallbackOrHole
    -> Int
    -> Int
    -> (List QueryCommand -> Int -> List QueryCommand)
    -> List QueryCallbackOrHole
doCallin old cbpos cipos fn =
    case (old,cbpos) of
        (QueryCallback(d) :: t, 0) -> (QueryCallback({d | commands = fn d.commands cipos})) :: t
        (h :: t, a) -> h :: (doCallin t (cbpos - 1) cipos fn)
        (nil, a) -> nil

addHole : List QueryCallbackOrHole -> Int -> List QueryCallbackOrHole
addHole old pos =
    case (old,pos) of
        (h :: old, 0) -> h :: QueryCallbackHole :: old
        (nil, 0) -> QueryCallbackHole :: nil
        (h :: t, a) -> h :: addHole t (a-1)
        (nil, a) -> nil

removeCOH : List a -> Int -> List a
removeCOH old pos =
    case (old,pos) of
        (h :: old, 0) -> old
        (h :: old, a) -> h :: (removeCOH old (a-1))
        (nil,a) -> nil

fillHole : List QueryCallbackOrHole -> number -> List QueryCallbackOrHole
fillHole old pos =
    case (old,pos) of
        (QueryCallbackHole :: old , 0) ->
            emptyCallback :: old
        (h :: old, a) -> h :: fillHole old (a-1)
        (nil,a) -> nil

--TODO: replace following two with doCallback

callbackSigSet
    : List QueryCallbackOrHole
    -> Int
    -> String
    -> List QueryCallbackOrHole
callbackSigSet cblist cbpos signature =
    case (cblist,cbpos) of
        (QueryCallback(d) :: t, 0) -> QueryCallback({d | signature = signature}) :: t
        (h :: t, a) -> h :: callbackSigSet t (cbpos - 1) signature
        (nil,a) -> nil

callbackFmwkSet
    : List QueryCallbackOrHole
    -> Int
    -> String
    -> List QueryCallbackOrHole
callbackFmwkSet cblist cbpos framework =
    List.indexedMap (\idx -> \v ->
        if idx == cbpos then
            case v of
                QueryCallback(v) -> QueryCallback ({v | frameworkClass = framework})
                QueryCallbackHole -> QueryCallbackHole
                QueryCallbackHoleResults(v) -> QueryCallbackHoleResults(v)
        else v
        ) cblist

iSetCallinFmwk : String -> List QueryCommand -> Int -> List QueryCommand
iSetCallinFmwk framework old pos =
    case (old,pos) of
        (QueryCallin(v) :: t, 0) -> QueryCallin({v | frameworkClass = framework}) :: t
        (h :: t, a) -> h :: (iSetCallinFmwk framework t (pos - 1))
        (nil, a) -> nil -- TODO: error state

iSetCallinSig : String -> List QueryCommand -> number -> List QueryCommand
iSetCallinSig sig old pos =
    case (old,pos) of
        (QueryCallin(v) :: t, 0) -> QueryCallin({v | signature = sig}) :: t
        (h :: t, a) -> h :: (iSetCallinSig sig t (pos-1))
        (nil, a) -> nil

iSetCallin: (QueryCallinData -> QueryCallinData)
    -> List QueryCommand
    -> Int
    -> List QueryCommand
iSetCallin opr old pos =
    case (old,pos) of
        (QueryCallin(v) :: t, 0) -> QueryCallin(opr v) :: t
        (h :: t, a) -> h :: (iSetCallin opr old pos)
        (nil, a) -> nil


doCallback: (QueryCallbackData -> QueryCallbackData) -> List QueryCallbackOrHole -> Int -> List QueryCallbackOrHole
doCallback opr old pos =
    case (old,pos) of
        (QueryCallback(v) :: t , 0) -> QueryCallback(opr v) :: t
        (h :: t, a) -> h :: (doCallback opr t (a-1))
        (nil, a) -> nil



type Msg
    = AddQueryCallbackAfter (Int)
    | AddQueryCallinAfter (Int, Int)
    | FillQueryCallbackHole (Int)
    | FillQueryCallinhole (Int,Int)
    | RemoveQueryCallback (Int)
    | RemoveQueryCallin (Int,Int)
    | SetCallbackInput (Int, String)
    | SetCallinInput (Int,Int, String)
    | SetParsedCallin(Int, Int, QueryCallinData)
    | SetParsedCallback(Int, QueryCallbackData)
    | UnSetParsedCallin(Int,Int)
    | UnSetParsedCallback(Int)
    | GetParsedCallback(Int,String)
    | SearchCallinHole (Int,Int)
    | ResponseCallinHole (Int, Int, List QueryCallbackData)

type Setter
    = QueryCallbackSig (Int, String)
    | QueryCallbackFmwk (Int,String)
    | QueryCallinSig (Int,Int, String)
    | QueryCallinFmwk (Int,Int, String)
    | QueryCallinRec (Int,Int, Param)
    | QueryCallinRet (Int,Int, Param)
    | QueryCallbackRec (Int, Param)

update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        AddQueryCallinAfter (callbackPos, callinPos) ->
            ({model | query = doCallin model.query callbackPos callinPos iAddCallin}, Cmd.none)
        AddQueryCallbackAfter(callbackPos) -> ({model | query = addHole model.query callbackPos}, Cmd.none)
        FillQueryCallbackHole(callbackPos) -> ({model | query = fillHole model.query callbackPos}, Cmd.none)
        FillQueryCallinhole(callbackPos, callinPos) ->
            ({model | query = doCallin model.query callbackPos callinPos iFill}, Cmd.none)
        RemoveQueryCallback(callbackPos) -> ({model | query = removeCOH model.query callbackPos}, Cmd.none)
        RemoveQueryCallin(callbackPos, callinPos) ->
            ({model | query = doCallin model.query callbackPos callinPos iRemoveCallin}, Cmd.none)
        SetParsedCallin(cbpos, cipos, d) ->
            ({model | query = doCallin model.query cbpos cipos (iSetCallin (\v -> d))},Cmd.none)
        SetParsedCallback(cbpos,d) ->
            ({model | query = doCallback (\v -> d) model.query cbpos}, Cmd.none)
        GetParsedCallback(cbpos, s) -> (model, parseCallback cbpos s) -- TODO
        SetCallbackInput(cbpos, s) -> ({model | query = doCallback (\v -> {v | input = s}) model.query cbpos}, Cmd.none)
        SetCallinInput(cbpos, cipos, s) ->
            ({model | query = doCallin model.query cbpos cipos (iSetCallin (\v -> {v | input = s}))},Cmd.none)
--        Set(QueryCallbackSig (cbpos, signature)) ->
--            ({model | query = callbackSigSet model.query cbpos signature}, Cmd.none)
--        Set(QueryCallbackFmwk (cbpos, framework)) ->
--            ({model |query = callbackFmwkSet model.query cbpos framework}, Cmd.none)
--        Set(QueryCallinSig (cbpos, cipos, sig)) ->
--            ({model | query = doCallin model.query cbpos cipos (iSetCallinSig sig)},Cmd.none)
--        Set(QueryCallinFmwk  (cbpos, cipos, framework)) ->
--            ({model | query = doCallin model.query cbpos cipos (iSetCallinFmwk framework)},Cmd.none)
--        Set(QueryCallinRec (cbpos, cipos, param)) ->
--            ({model | query = doCallin model.query cbpos cipos (iSetCallin (\v -> {v | receiver = param}))}, Cmd.none)
--        Set(QueryCallinRet (cbpos, cipos, param)) ->
--            ({model | query = doCallin model.query cbpos cipos (iSetCallin (\v -> {v | return = param}))}, Cmd.none)
--        Set(QueryCallbackRec (cbpos, param)) ->
--            ({model | query = doCallback (\v -> {v | receiver = param}) model.query cbpos }, Cmd.none)
        SearchCallinHole (cbpos, cipos) -> (model, Cmd.none) -- TODO
        ResponseCallinHole (cbpos, cipos, callbacks) -> (model, Cmd.none) --TODO
        UnSetParsedCallback (cbpos) ->
            ({model | query = doCallback (\v -> {v | parsed = False}) model.query cbpos}, Cmd.none)
        UnSetParsedCallin (cbpos, cipos) ->
            ({model | query = doCallin model.query cbpos cipos (iSetCallin (\v -> {v | parsed = False}))}, Cmd.none)


-- View

sp : Block.Item msg
sp =
    Block.custom (text " ")

newline : Block.Item msg
newline =
    Block.custom (Html.br [] [])


holeCard : Int -> Card.Config Msg -> Card.Config Msg
holeCard pos =
    Card.block []
                [ Block.titleH6 [] [ text "Hole" ]
                , Block.custom <|
                    Button.button [ Button.primary, Button.onClick (AddQueryCallbackAfter pos)] [ text "+" ]
                , sp
                , Block.custom <|
                    Button.button [ Button.primary, Button.onClick (RemoveQueryCallback pos) ] [ text "-" ]
                , sp
                , Block.custom <|
                    Button.button [ Button.secondary, Button.onClick (FillQueryCallbackHole pos) ] [ text "Fill" ]
                , sp
                , Block.custom <|
                    Button.button [ Button.primary] [ text "Search"]

                ]

inputBox : QueryCallbackData -> Input.Option msg -> List (Input.Option msg)
inputBox d upd=
    case (d.parsed, d.input) of
        (False,"") -> [ Input.placeholder "--input method query--", upd]
        (False, s) -> [ Input.value s, upd ]
        (True, s) -> [ Input.value s, upd ]
ciInputBox : QueryCallinData -> Input.Option msg -> List (Input.Option msg)
ciInputBox d upd=
    case (d.parsed, d.input) of
        (False,"") -> [ Input.placeholder "--input method query--", upd]
        (False, s) -> [ Input.value s, upd ]
        (True, s) -> [ Input.value s, upd ]

callbackCard : QueryCallbackData -> Int -> Card.Config Msg -> Card.Config Msg
callbackCard d pos =
    Card.block []
                (
                    [ -- Block.titleH4 [] [ text "Callback" ]
                        Block.custom <|
                            Input.text (inputBox d (Input.onInput (\s -> SetCallbackInput(pos, s))))
                        , Block.custom <|
                            Checkbox.checkbox [Checkbox.onCheck (\b ->
                                if b then
                                    GetParsedCallback(pos, d.input)
                                else
                                    UnSetParsedCallback(pos)
                                )] "Set"
--                        , Block.custom (text "Signature")
--                        ,Block.custom <|
--                            Input.text [ Input.value d.signature
--                                ,Input.onInput (\sig -> Set(QueryCallbackSig (pos, sig))) ]
----                        , Block.custom <| Button.button [ Button.primary ] [ text "Set" ]
----                        , newline, sp, newline
--                        , Block.custom (text "Framework Object")
--                        , Block.custom <|
--                            Input.text [ Input.value d.frameworkClass
--                                ,Input.onInput <| \fmwk -> Set(QueryCallbackFmwk (pos,fmwk)) ]
--                        , Block.custom (text "Receiver")
--                        , Block.custom <|
--                            Input.text [paramString d.receiver
--                                , Input.onInput <| \name -> Set(QueryCallbackRec (pos, NamedVar(name) ))]
--                        , newline
                    ]
                    ++

                    (List.indexedMap (\i -> \a -> Block.custom (callinOrHoleCard pos i a) ) d.commands) ++

                    [ newline, Block.custom <|
                        Button.button [
                            Button.primary, Button.onClick (AddQueryCallinAfter (pos, -1))
                        ] [ text "+ callin"]
                    , sp
                    , Block.custom <|
                        Button.button [ Button.primary, Button.onClick (AddQueryCallbackAfter pos)  ] [ text "+ callback" ]
                    , sp
                    , Block.custom <|
                        Button.button [ Button.primary, Button.onClick (RemoveQueryCallback pos) ] [text "- callback"]

                    ]
                )

callinButtons : Int -> Int -> Card.Config Msg -> Card.Config Msg
callinButtons cbpos cipos =
    Card.block []
        [
            Block.custom <|
                Button.button [ Button.primary, Button.onClick (RemoveQueryCallin (cbpos,cipos)) ] [ text "- callin"]
            ,sp
            ,Block.custom <|
                Button.button [ Button.primary, Button.onClick (AddQueryCallinAfter (cbpos,cipos)) ] [ text "+ after"]
            ,sp
        ]

callinOrHoleAttrs : List (Attribute msg)
callinOrHoleAttrs = [ style [ ( "width", "25rem" ) ] ]

paramString : Param -> Input.Option msg
paramString p =
    case p of
        NamedVar(s) -> Input.value s
        Hole -> Input.placeholder "***hole***"

callinCard : QueryCallinData -> Int -> Int -> Html Msg
callinCard callin cbpos cipos =
        Card.config [ Card.attrs callinOrHoleAttrs ]
            |> Card.header [ class "text-center" ]
                [ h5 [ ] [ text "Callin" ]
                ]
            |> Card.block []
                [
                    Block.custom <|
                        Input.text  (ciInputBox callin (Input.onInput (\s -> SetCallinInput(cbpos, cipos, s))))
--                    Block.custom <|
--                        Input.text [ Input.value callin.signature
--                            , Input.onInput (\sig -> Set(QueryCallinSig (cbpos, cipos, sig)))]
--                    , Block.custom (text "Framework Object")
--                    , Block.custom <|
--                        Input.text [ Input.value callin.frameworkClass
--                            , Input.onInput (\fmwk -> Set(QueryCallinFmwk (cbpos, cipos, fmwk)))]
--                    , Block.custom (text "Receiver")
--                    , Block.custom <|
--                        Input.text [ paramString callin.receiver
--                            , Input.onInput (\name -> Set(QueryCallinRec (cbpos, cipos, NamedVar(name) )))]
--                    , Block.custom (text "Return")
--                    , Block.custom <|
--                        Input.text [ paramString callin.return
--                            , Input.onInput (\name -> Set(QueryCallinRet (cbpos, cipos, NamedVar(name) )))]
                ]
            |> callinButtons cbpos cipos
            |> Card.view

callinHoleCard : Int -> Int -> Html Msg
callinHoleCard cbpos cipos =
        Card.config [ Card.attrs callinOrHoleAttrs ]
            |> Card.header [ class "text-center" ]
                [ h5 [ ] [ text "Callin Hole" ]
                ]

            |> callinButtons cbpos cipos
            |> Card.block [] [
                Block.custom <|
                      Button.button [ Button.secondary, Button.onClick (FillQueryCallinhole (cbpos,cipos)) ] [ text "Fill"]
                , sp
                , Block.custom <|
                      Button.button [ Button.secondary, Button.onClick (SearchCallinHole (cbpos, cipos))] [text "Search"]
            ]
            |> Card.view


callinOrHoleCard : Int -> Int -> QueryCommand -> Html Msg
callinOrHoleCard cbpos cipos c =
    case c of
        QueryCallin(d) -> callinCard d cbpos cipos
        QueryCommandHole -> callinHoleCard cbpos cipos

callbackOhrHoleCard : (Card.Config msg -> Card.Config msg1) -> Html msg1
callbackOhrHoleCard contents =
    Card.config [ Card.attrs [ style [ ( "width", "30rem" ) ] ] ]
        |> Card.header [ class "text-center" ]
            [ h6 [ ] [ text "Callback" ]
            ]
        |> contents
        |> Card.view

drawCallbackOrHole : Int -> QueryCallbackOrHole -> Html Msg
drawCallbackOrHole pos c =
    case c of
        QueryCallback(d) -> callbackOhrHoleCard (callbackCard d pos)
        QueryCallbackHole -> callbackOhrHoleCard (holeCard pos)
        QueryCallbackHoleResults(v) -> callbackOhrHoleCard (holeCard pos) --TODO: display results


view : Model -> Html Msg
view model =
    Grid.container []
        (CDN.stylesheet :: (List.indexedMap drawCallbackOrHole model.query))
--        , Grid.row[] [ Grid.col [] [ text ".."] ]
--        , Grid.row[] [ Grid.col [] [ text "..."] ]



-- SUBSCRIPTIONS
subscriptions : Model -> Sub Msg
subscriptions model =
    Sub.none

-- HTTP
--reqHdr : String -> Http.Body -> Decode.Decoder a -> Http.Request a
reqHdr url body decoder =
  Http.request
    { method = "POST"
    , headers = [] --[Http.header "Content-Type" "application/json"]
    , url = url
    , body = body
    , expect = Http.expectJson decoder
    , timeout = Nothing
    , withCredentials = False
    }
-- get callin and callback
parsedCallbackResponse : Int -> Result Http.Error Qt.CMessage -> Msg
parsedCallbackResponse cbpos result =
    case result of
        Ok(v) -> SetParsedCallback(cbpos, { frameworkClass = ""
                                                  , signature = ""
                                                  , receiver = Hole
                                                  , return = Hole, commands = [], input="", parsed = False, params = []}) -- TODO: set parse result
        Err(v) -> UnSetParsedCallback(cbpos)



parseCallback : Int -> String -> Cmd Msg
parseCallback cbpos input =
    Http.send (parsedCallbackResponse cbpos) <|
        reqHdr "/parse_ls"
            (Http.jsonBody (Encode.object [("specline", Encode.string input)] ))
            (Qt.cMessageDecoder)

--getCallinCompletionSearch : Maybe Int -> Maybe Int -> List QueryCallbackOrHole -> List Qt.CTrace
--getCallinCompletionSearch cbpos cipos query =
--


-- Serialization

queryParamAsQ : Param -> Maybe Qt.CParam
queryParamAsQ p =
    case p of
        NamedVar(s) -> Just {param = Qt.Variable ({name = s}) }
        Hole -> Just {param = Qt.PrHole(Qt.Hole False)}

queryCommandAsQ : QueryCommand -> Bool -> Qt.CCommand
queryCommandAsQ cmd select =
    case cmd of
        QueryCallin(d) -> {
            ciCommand = Qt.Callin {methodSignature = d.signature, --
                frameworkClass = d.frameworkClass,
                parameters = [], --TODO
                receiver = queryParamAsQ d.receiver,
                returnValue = queryParamAsQ d.return,
                exception = Nothing,
                nestedCallbacks = []} }
        QueryCommandHole -> {ciCommand = Qt.CiHole (Qt.Hole select)}

queryCallbackOrHoleAsQ : QueryCallbackOrHole -> Maybe Int -> Bool -> Qt.CallbackOrHole
queryCallbackOrHoleAsQ cb opt_cipos selected_callback =
    case cb of
        QueryCallbackHole -> {cbCommand = Qt.CbHole {isSelected = selected_callback}}
        QueryCallbackHoleResults(d) -> {cbCommand = Qt.CbHole {isSelected = False}}
        QueryCallback(d) -> {cbCommand = Qt.Callback { methodSignature = d.signature,
            firstFrameworkOverrrideClass = d.frameworkClass,
            applicationClass = "",
            parameters = [],
            receiver = queryParamAsQ d.receiver,
            returnValue = Nothing,
            exception = Nothing,
            nestedCommands = (
                case opt_cipos of
                    Just(v) -> List.indexedMap (\idx -> \cmd -> queryCommandAsQ cmd (idx == v)) d.commands
                    Nothing -> List.map (\cmd -> queryCommandAsQ cmd False) d.commands
            )}}

queryAsQ : Maybe Int -> Maybe Int -> List QueryCallbackOrHole -> Qt.CTrace
queryAsQ cbpos cipos query =
    let
        cbs =
            case (cbpos,cipos) of
                (Nothing, cipos) -> List.map (\cb -> queryCallbackOrHoleAsQ cb cipos False) query
                (Just cbpos, Nothing) ->
                    List.indexedMap (\idx -> \cb -> queryCallbackOrHoleAsQ cb Nothing (idx == cbpos)) query
                (Just cbpos, Just cipos) ->
                    List.indexedMap (\idx -> \cb ->
                        queryCallbackOrHoleAsQ cb (if idx == cbpos then Just cipos else Nothing) False) query
    in
        {id = Nothing, callbacks = cbs}