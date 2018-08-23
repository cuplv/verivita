module TraceQuery exposing (..)

import Html exposing (..)
import Html.Events
import Http
import Json.Decode as Decode
import Json.Encode as Encode
import Bootstrap.CDN as CDN
import Bootstrap.Card as Card
import Bootstrap.Card.Block as Block
import Bootstrap.Dropdown as Dropdown
import Bootstrap.Grid as Grid
import Html.Attributes exposing (class, src, style)
import Bootstrap.Button as Button
import Bootstrap.Form.Input as Input
import Bootstrap.Form.Checkbox as Checkbox
import QueryTrace as Qt
import Debug


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
    | QueryCommandHoleResults(List QueryCallinData)
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
        querySelectionList : List String,
        querySelectDropDownState : Dropdown.State,
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
    ( Model [] Dropdown.initialState [QueryCallbackHole],  getQueryList)


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
    | SetCallinHoleResults(Int,Int, List QueryCallinData)
    | UnSetParsedCallin(Int,Int)
    | UnSetParsedCallback(Int)
    | GetParsedCallback(Int, QueryCallbackData)
    | GetParsedCallin(Int, Int, QueryCallinData)
    | SearchCallinHole (Int,Int)
    | ResponseCallinHole (Int, Int, List QueryCallbackData)
    | DisplayCallbackError(Int,String)
    | DisplayCallinError(Int, Int, String)
    | GetQueryList
    | SetQueryList(List String)
    | QuerySelectDropToggle Dropdown.State
    | SetQuerySelection String
    | SetQuery (List QueryCallbackOrHole)


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
        GetParsedCallback(cbpos, oldcbdat) -> (model, parseCallback cbpos oldcbdat)
        GetParsedCallin(cbpos, cipos, oldcidat) -> (model, parseCallin cbpos cipos oldcidat)
        SetCallbackInput(cbpos, s) -> ({model | query = doCallback (\v -> {v | input = s}) model.query cbpos}, Cmd.none)
        SetCallinInput(cbpos, cipos, s) ->
            ({model | query = doCallin model.query cbpos cipos (iSetCallin (\v -> {v | input = s}))},Cmd.none)
        SearchCallinHole (cbpos, cipos) -> (model, searchCallinHole cbpos cipos model.query) -- TODO
        ResponseCallinHole (cbpos, cipos, callbacks) -> (model, Cmd.none) --TODO
        UnSetParsedCallback (cbpos) ->
            ({model | query = doCallback (\v -> {v | parsed = False}) model.query cbpos}, Cmd.none)
        UnSetParsedCallin (cbpos, cipos) ->
            ({model | query = doCallin model.query cbpos cipos (iSetCallin (\v -> {v | parsed = False}))}, Cmd.none)
        SetCallinHoleResults(cbpos,cipos, resList) ->
            ({model | query = doCallinHole model.query cbpos cipos resList}, Cmd.none)
        DisplayCallbackError(cbpos, string) -> (model,Cmd.none) --TODO
        DisplayCallinError(cbpos, cipos, string) ->
            (model, Cmd.none) -- TODO
        SetQueryList(l) -> ({model | querySelectionList = l},Cmd.none)
        GetQueryList -> (model, getQueryList)
        QuerySelectDropToggle t -> ({model | querySelectDropDownState = t}, Cmd.none)
        SetQuerySelection name -> (model, getQuery name)
        SetQuery q -> ({model | query = q}, Cmd.none)

iDoCallinHole : List QueryCommand -> Int -> List QueryCallinData -> List QueryCommand
iDoCallinHole olist cipos res =
    List.indexedMap (\idx -> \v ->
        (case (idx, v) of
            (cipos, QueryCommandHole) -> QueryCommandHoleResults(res)
            (a,b) -> b
        )) olist

doCallinHole : List QueryCallbackOrHole -> Int -> Int -> List QueryCallinData -> List QueryCallbackOrHole
doCallinHole olist cbpos cipos res =
    List.indexedMap (\idx -> \v ->
        ( case (idx, v) of
            (cbpos, QueryCallback(d)) -> QueryCallback({d | commands = iDoCallinHole d.commands cipos res})
            (a,b) -> b --TODO: callins within callback holes
        )) olist

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
                                    GetParsedCallback(pos, d)
                                else
                                    UnSetParsedCallback(pos)
                                )] "Set"
                        , Block.custom <|
                            text (if d.parsed then "set" else "unset")
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
callinOrHoleAttrs = [ style [ ( "width", "55rem" ) ] ]

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
                    , Block.custom <|
                        Checkbox.checkbox [Checkbox.onCheck (\b ->
                            if b then
                                GetParsedCallin(cbpos, cipos, callin)
                            else
                                UnSetParsedCallin(cbpos,cipos)
                            )] "Set"
                    , Block.custom <|
                        text (if callin.parsed then "set" else "unset")
                ]
            |> callinButtons cbpos cipos
            |> Card.view


resultListDisplay : Maybe a -> Card.Config msg -> Card.Config msg
resultListDisplay resultDat =
    Card.block []
        (case resultDat of
            Just v -> [Block.custom <| text "..."] -- TODO: display results
            Nothing -> []
        )



callinHoleCard : Int -> Int -> Maybe (List QueryCallinData) -> Html Msg
callinHoleCard cbpos cipos resultDat =
        Card.config [ Card.attrs callinOrHoleAttrs ]
            |> Card.header [ class "text-center" ]
                [ h5 [ ] [ text "Callin Hole" ]
                ]

            |> resultListDisplay resultDat

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
        QueryCommandHole -> callinHoleCard cbpos cipos Nothing
        QueryCommandHoleResults(r) -> callinHoleCard cbpos cipos (Just r)

callbackOhrHoleCard : (Card.Config msg -> Card.Config msg1) -> Html msg1
callbackOhrHoleCard contents =
    Card.config [ Card.attrs [ style [ ( "width", "60rem" ) ] ] ]
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


queryHeader : Model -> Html Msg
queryHeader model =
    Grid.container []
        [ Grid.row [] (List.map (\a -> Grid.col [] [a])
            [ Dropdown.dropdown model.querySelectDropDownState
                {
                    options = [ ]
                    , toggleMsg = QuerySelectDropToggle
                    , toggleButton =
                        Dropdown.toggle [ Button.primary ] [ text "Select Pre Defined Query" ]
                    , items = List.map (\name -> Dropdown.buttonItem [ Html.Events.onClick <| SetQuerySelection name ] [text name] ) model.querySelectionList
                }
            , Button.button [Button.primary] [ text "Verify" ]
            , Button.button [Button.primary] [ text "Search Traces" ] ] )
         , Grid.row [] [ Grid.col [][text " "] ] ] --TODO: pad with some space

view : Model -> Html Msg
view model =
    Grid.container []
        (CDN.stylesheet
            :: (queryHeader model)
            :: (List.indexedMap drawCallbackOrHole model.query))
--        , Grid.row[] [ Grid.col [] [ text ".."] ]
--        , Grid.row[] [ Grid.col [] [ text "..."] ]



-- SUBSCRIPTIONS
subscriptions : Model -> Sub Msg
subscriptions model =
    Sub.none

-- HTTP
--reqHdr : String -> Http.Body -> Decode.Decoder a -> Http.Request a
reqHdr : String -> Http.Body -> Decode.Decoder a -> Http.Request a
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

parsedCallinResponse : Int -> Int -> QueryCallinData -> Result Http.Error Qt.CMessage -> Msg
parsedCallinResponse cbpos cipos oldcb result =
    case result of
        Ok(result) ->
            case result.msg of
                Qt.MCallin(v) ->
                    SetParsedCallin(cbpos, cipos, { frameworkClass = v.frameworkClass
                                                        , signature = v.methodSignature
                                                        , receiver = qoAsQueryParam v.receiver
                                                        , return = qoAsQueryParam v.returnValue
                                                        , input = oldcb.input
                                                        , parsed = True
                                                        , params = List.map qAsQueryParam v.parameters })
                Qt.MCallback(v) -> UnSetParsedCallin(cbpos, cipos)
                Qt.MProblem(v) -> UnSetParsedCallin(cbpos,cipos)
                Qt.MsgUnspecified -> UnSetParsedCallin(cbpos,cipos)
        Err(v) -> UnSetParsedCallin(cbpos,cipos)


parsedCallbackResponse : Int -> QueryCallbackData -> Result Http.Error Qt.CMessage -> Msg
parsedCallbackResponse cbpos oldcb result =
    case result of
        Ok(result) ->
            case result.msg of
                Qt.MCallback(v) ->
                    SetParsedCallback(cbpos, { frameworkClass = v.firstFrameworkOverrrideClass
                                                          , signature = v.methodSignature
                                                          , receiver = qoAsQueryParam v.receiver
                                                          , return = qoAsQueryParam v.returnValue
                                                          , commands = oldcb.commands
                                                          , input = oldcb.input
                                                          , parsed = True
                                                          , params = List.map qAsQueryParam v.parameters })
                Qt.MProblem(p) -> UnSetParsedCallback(cbpos)
                Qt.MCallin(v) -> UnSetParsedCallback(cbpos)
                Qt.MsgUnspecified -> UnSetParsedCallback(cbpos)

        Err(v) -> UnSetParsedCallback(cbpos) --TODO: display error

setCallinHoleResults : Int -> Int -> Result Http.Error Qt.CMessageList -> Msg
setCallinHoleResults cbpos cipos result =
    case result of
        Ok(result) -> SetCallinHoleResults(cbpos, cipos, cMessageListAsCallinHole result)
        Err(v) -> DisplayCallinError(cbpos, cipos, "http error") -- TODO: display error

setQueryList : Result Http.Error (List String) -> Msg
setQueryList result =
    case result of
        Ok(lst) -> SetQueryList(lst)
        Err(v) -> SetQueryList([]) --TODO: display better error than empty list

setQuery : Result Http.Error Qt.CTrace -> Msg
setQuery result =
    case result of
        Ok(ctr) -> SetQuery(cTraceAsQuery ctr)
        Err(v) -> SetQuery([]) -- TODO: display error

getQueryList : Cmd Msg
getQueryList =
    Http.send setQueryList <| Http.get "/query_list" (Decode.list Decode.string)



getQuery : String -> Cmd Msg
getQuery name =
    Http.send setQuery <| Http.get ("/get_query/" ++ name) Qt.cTraceDecoder

searchCallinHole : Int -> Int -> List QueryCallbackOrHole -> Cmd Msg
searchCallinHole cbpos cipos model =
        Http.send (setCallinHoleResults cbpos cipos)
            (reqHdr "/completion_search"
                (Http.jsonBody <| Qt.cTraceEncoder <| queryAsQ (Just cbpos) (Just cipos) model)
                Qt.cMessageListDecoder)

parseCallback : Int -> QueryCallbackData -> Cmd Msg
parseCallback cbpos input =
    Http.send (parsedCallbackResponse cbpos input) <|
        reqHdr "/parse_ls"
            (Http.jsonBody (Encode.object [("specline", Encode.string input.input)
                , ("msg", Encode.string "callback")]))
            (Qt.cMessageDecoder)
parseCallin : Int -> Int -> QueryCallinData -> Cmd Msg
parseCallin cbpos cipos cbdat =
    Http.send (parsedCallinResponse cbpos cipos cbdat) <|
        reqHdr "/parse_ls"
            (Http.jsonBody (Encode.object [("specline", Encode.string cbdat.input)
                , ("msg", Encode.string "callin")]))
            (Qt.cMessageDecoder)

--getCallinCompletionSearch : Maybe Int -> Maybe Int -> List QueryCallbackOrHole -> List Qt.CTrace
--getCallinCompletionSearch cbpos cipos query =
--

-- Deserialization

cTraceAsQuery: Qt.CTrace -> List QueryCallbackOrHole
cTraceAsQuery ctrace =
    List.map (\c -> cCommandAsQueryCallbackOrHole c.cbCommand) ctrace.callbacks


cCommandAsQueryCallbackOrHole : Qt.CbCommand -> QueryCallbackOrHole
cCommandAsQueryCallbackOrHole c =
    case c of
        Qt.CbCommandUnspecified -> QueryCallbackHole
        Qt.Callback(c) -> cCallbackAsQuery c
        Qt.CbHole(h) -> QueryCallbackHole

queryParamToInput : Param -> String
queryParamToInput p =
    case p of
        NamedVar(n) -> n
        Hole -> "#"

queryFrameworkClassToInput : List Param -> String -> String
queryFrameworkClassToInput params fmwk =
    let
        parstrings = List.map queryParamToInput params
        parsplit = String.split "(" fmwk
    in
        case parsplit of
            front :: paramtypes :: t ->
                let
                    zpars = List.map2 (\pstr -> \ptyp -> pstr ++ " : " ++ ptyp) parstrings (String.split "," paramtypes)
                    pjoin = String.join " , " zpars
                in
                    front ++ ("(" ++ pjoin) -- ++ "   DBG: " ++ (List.head (String.split "," paramtypes))
            nil -> "error"

queryCallbackDataToInput : QueryCallbackData -> String
queryCallbackDataToInput qc =
    let
        rval = queryParamToInput qc.return
        rec = queryParamToInput qc.receiver
    in
        rval ++ " = [" ++ rec ++ "] " ++ (queryFrameworkClassToInput qc.params qc.frameworkClass)
queryCallinDataToInput : QueryCallinData -> String
queryCallinDataToInput qc =
    let
        rval = queryParamToInput qc.return
        rec = queryParamToInput qc.receiver
    in
        rval ++ " = [" ++ rec ++ "] " ++ (queryFrameworkClassToInput qc.params qc.frameworkClass)

cCallbackAsQuery : Qt.CCallback -> QueryCallbackOrHole
cCallbackAsQuery c =
    let d = { frameworkClass = c.firstFrameworkOverrrideClass
                        , signature = c.methodSignature
                        , input = ""
                        , parsed = True
                        , receiver = qoAsQueryParam c.receiver
                        , return = qoAsQueryParam c.returnValue
                        , commands = List.map cCommandAsQueryCommand c.nestedCommands
                        , params = List.map qAsQueryParam c.parameters
                    }
    in
        QueryCallback( {d | input = queryCallbackDataToInput d} )

cCommandAsQueryCommand : Qt.CCommand -> QueryCommand
cCommandAsQueryCommand c =
    case c.ciCommand of
        Qt.CiCommandUnspecified -> QueryCommandHole
        Qt.Callin(c) -> QueryCallin(cCallinAsQuery c)
        Qt.CiHole(_) -> QueryCommandHole

cMessageListAsCallinHole : Qt.CMessageList -> List QueryCallinData
cMessageListAsCallinHole c =
        List.filterMap cMessageAsQueryCallinData c.msgs


cCallinAsQuery v =
    let
        d = {frameworkClass = v.frameworkClass
            , signature = v.methodSignature
            , input = "auto fill"
            , parsed = True
            , receiver = qoAsQueryParam v.receiver
            , return = qoAsQueryParam v.returnValue
            , params = List.map qAsQueryParam v.parameters}
    in
        {d | input = queryCallinDataToInput d}

cMessageAsQueryCallinData : Qt.CMessage -> Maybe QueryCallinData
cMessageAsQueryCallinData m =
    case m.msg of
        Qt.MCallin(v) -> Just <| cCallinAsQuery v
        _ -> Nothing


qoAsQueryParam : Maybe Qt.CParam -> Param
qoAsQueryParam p =
    case p of
        Just(p) -> qAsQueryParam p
        Nothing -> Hole

qAsQueryParam : Qt.CParam -> Param
qAsQueryParam p =
    case p.param of
        Qt.Variable(cvar) -> NamedVar(cvar.name)
        _ -> Hole



-- Serialization

queryParamAsQ : Param -> Qt.CParam
queryParamAsQ p =
    case p of
        NamedVar(s) -> {param = Qt.Variable ({name = s}) }
        Hole -> {param = Qt.PrHole(Qt.Hole False)}



queryCommandAsQ : QueryCommand -> Bool -> Qt.CCommand
queryCommandAsQ cmd select =
    case cmd of
        QueryCallin(d) -> {
            ciCommand = Qt.Callin {methodSignature = d.signature, --
                frameworkClass = d.frameworkClass,
                parameters =  List.map queryParamAsQ d.params,
                receiver = Just <| queryParamAsQ d.receiver,
                returnValue = Just <| queryParamAsQ d.return,
                exception = Nothing,
                nestedCallbacks = []} }
        QueryCommandHole -> {ciCommand = Qt.CiHole (Qt.Hole select)}
        QueryCommandHoleResults(r) -> {ciCommand = Qt.CiHole (Qt.Hole select)}

queryCallbackOrHoleAsQ : QueryCallbackOrHole -> Maybe Int -> Bool -> Qt.CallbackOrHole
queryCallbackOrHoleAsQ cb opt_cipos selected_callback =
    case cb of
        QueryCallbackHole -> {cbCommand = Qt.CbHole {isSelected = selected_callback}}
        QueryCallbackHoleResults(d) -> {cbCommand = Qt.CbHole {isSelected = False}}
        QueryCallback(d) -> {cbCommand = Qt.Callback { methodSignature = d.signature,
            firstFrameworkOverrrideClass = d.frameworkClass,
            applicationClass = "",
            parameters = List.map queryParamAsQ d.params,
            receiver = Just <| queryParamAsQ d.receiver,
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