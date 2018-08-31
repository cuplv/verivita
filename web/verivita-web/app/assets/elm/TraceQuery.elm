module TraceQuery exposing (..)

import Html exposing (..)
import Html.Events exposing (onClick)
import Http
import Json.Decode as Decode
import Json.Decode.Pipeline as Pipeline
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
import Bootstrap.Utilities.Spacing as Spacing
import Bootstrap.Utilities.Size as Size
import Bootstrap.Grid.Col as Col
import Bootstrap.Grid.Row as Row
import Bootstrap.ListGroup as ListGroup
import Bootstrap.Badge as Badge
import QueryTrace as Qt
import Debug
import Time exposing (Time)
import Dict
import Html.Attributes as Attributes


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
    | BooleanPrimitive(Bool)
    | IntegerPrimitive(Int)
    | LongPrimitive(Int)
    | StringPrimitive(String)
    | Hole


type QueryCallbackOrHole = QueryCallback(QueryCallbackData)
    | QueryCallbackHole
    | QueryCallbackHoleResults(List QueryCallbackData)


type ParseStatus
    = NotParsed(Float)
    |Parsed
    |ParseError
type alias QueryCallbackData =
    {
        frameworkClass : String,
        signature : String,
        input : String, -- Nothing when parsed successfully Just "" initially
        parsed : ParseStatus,
        receiver : Param,
        commands : List QueryCommand,
        params : List Param,
        return : Param
    }

type QueryCommand
    = QueryCallin(QueryCallinData)
    | QueryCommandHole
    | QueryCommandHoleResults(List RankedMessage)
type alias QueryCallinData =
    {
        frameworkClass: String,
        signature : String,
        input : String, -- Nothing when parsed successfully Just "" initially
        parsed : ParseStatus,
        receiver : Param,
        params : List Param,
        return : Param
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

type alias RankedMessage =
    {
        rank : Int
        , msg : MessageResponse
    }
type MessageResponse
    = MessageResponseCi(QueryCallinData)
    | MessageResponseCb(QueryCallbackData)


type VerificationResults
    = VerificationError String
    | VerificationSafe
    | VerificationUnsafe (List QueryCallbackOrHole)
    | VerificationPending(Int)
    | VerificationNoResults

type ResultsTab
    = ResultsVerify (Maybe Int)
    | ResultsSearch

type alias Model =
    {
        querySelectionList : List String,
        disallowSelectionList : (Dict.Dict String VerificationResults),
        querySelectDropDownState : Dropdown.State,
        query : List QueryCallbackOrHole,
        resultsTabSelected : ResultsTab,
        ctime : Float,
        queryDescription : String
    }

-- initial callback and callin set to parse error so no parse until something reasonable is entered
emptyCallback : QueryCallbackOrHole
emptyCallback =
    QueryCallback( { frameworkClass = ""
        , signature = ""
        , receiver = Hole
        , return = Hole, commands = [], input="", parsed = ParseError, params = []})

emptyCallinDat : QueryCallinData
emptyCallinDat =
    { frameworkClass = ""
            , signature = ""
            , receiver = Hole , return = Hole, input="", parsed = ParseError, params = []}

emptyCallin : QueryCommand
emptyCallin =
    QueryCallin(emptyCallinDat)

init : ( Model, Cmd Msg)
init =
    ( Model [] Dict.empty
        Dropdown.initialState
        [QueryCallbackHole]
        (ResultsVerify Nothing)
        (1/0)
        ""
        , Cmd.batch [getQueryList, getDisallowList])


-- UPDATE
incrCxe : ResultsTab -> ResultsTab
incrCxe c =
    case c of
        ResultsSearch -> ResultsVerify(Just 0)
        ResultsVerify Nothing -> ResultsVerify(Just 0)
        ResultsVerify (Just n) -> ResultsVerify (Just (n + 1))
decrCxe : ResultsTab -> ResultsTab
decrCxe c =
    case c of
        ResultsSearch -> ResultsVerify(Just 0)
        ResultsVerify Nothing -> ResultsVerify(Just 0)
        ResultsVerify (Just n) -> ResultsVerify (Just (n - 1))



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
        (nil,a) -> Debug.crash "mismatched list length fillHole"

iSetCallin: (QueryCallinData -> QueryCallinData)
    -> List QueryCommand
    -> Int
    -> List QueryCommand
iSetCallin opr old pos =
    case (old,pos) of
        (QueryCallin(v) :: t, 0) -> QueryCallin(opr v) :: t
        (QueryCommandHole :: t, 0) -> QueryCallin(opr emptyCallinDat) :: t
        (QueryCommandHoleResults(r) :: t, 0) -> QueryCallin(opr emptyCallinDat) :: t
        (h :: t, a) -> h :: (iSetCallin opr t (pos - 1))
        (nil, a) -> Debug.crash "mismatched list length iSetCallin"


doCallback: (QueryCallbackData -> QueryCallbackData) -> List QueryCallbackOrHole -> Int -> List QueryCallbackOrHole
doCallback opr old pos =
    case (old,pos) of
        (QueryCallback(v) :: t , 0) -> QueryCallback(opr v) :: t
        (h :: t, a) -> h :: (doCallback opr t (a-1))
        (nil, a) -> Debug.crash "mismatched list length doCallback"



type Msg
    =
    -- User Input Model Updates
    AddQueryCallbackAfter (Int)
    | AddQueryCallinAfter (Int, Int)
    | FillQueryCallbackHole (Int)
    | FillQueryCallinhole (Int,Int)
    | RemoveQueryCallback (Int)
    | RemoveQueryCallin (Int,Int)
    | SetCallbackInput (Int, String)
    | SetCallinInput (Int,Int, String)
    | UnSetParsedCallin(Int,Int)
    | UnSetParsedCallback(Int)
    | QuerySelectDropToggle Dropdown.State
    | Nop
    | SelectResultsTab ResultsTab
    | ParseAll(Float)
    | DecrCxe
    | IncrCxe

    -- Update From Http Requests
    | SetParsedCallin(Int, Int, QueryCallinData)
    | SetParsedCallback(Int, QueryCallbackData)
    | SetCallinHoleResults(Int,Int, List RankedMessage)
    | DisplayCallbackError(Int,String)
    | DisplayCallinError(Int, Int, String)
    | SetQueryList(List String)
    | SetDisallowList(List String)
    | SetQuerySelection String
    | SetQuery (List QueryCallbackOrHole)
    | SetVerificationResults (String, VerificationResults)
    | SetQueryDescription(String)

    -- Send Http Requests
    | GetParsedCallback(Int, QueryCallbackData)
    | GetParsedCallin(Int, Int, QueryCallinData)
    | SearchCallinHole (Int,Int)
    | GetQueryList
    | GetDisallowList
    | GetVerificationResults (String, Int) -- periodic update checks for results --TODO: swap with id, add timer to trigger and update
    | PostVerificationTask (String) -- initialize the verification with a rule
    | GetQueryDescription(String)



update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        AddQueryCallinAfter (callbackPos, callinPos) ->
            ({model | query = doCallin model.query callbackPos callinPos iAddCallin
                ,disallowSelectionList = deselectQueryResults model.disallowSelectionList
            }, Cmd.none)
        AddQueryCallbackAfter(callbackPos) -> ({model | query = addHole model.query callbackPos
                ,disallowSelectionList = deselectQueryResults model.disallowSelectionList
            }, Cmd.none)
        FillQueryCallbackHole(callbackPos) -> ({model | query = fillHole model.query callbackPos
                ,disallowSelectionList = deselectQueryResults model.disallowSelectionList
            }, Cmd.none)
        FillQueryCallinhole(callbackPos, callinPos) ->
            ({model | query = doCallin model.query callbackPos callinPos iFill
                ,disallowSelectionList = deselectQueryResults model.disallowSelectionList
            }, Cmd.none)
        RemoveQueryCallback(callbackPos) -> ({model | query = removeCOH model.query callbackPos
                ,disallowSelectionList = deselectQueryResults model.disallowSelectionList
            }, Cmd.none)
        RemoveQueryCallin(callbackPos, callinPos) ->
            ({model | query = doCallin model.query callbackPos callinPos iRemoveCallin
                ,disallowSelectionList = deselectQueryResults model.disallowSelectionList
            }, Cmd.none)
        SetParsedCallin(cbpos, cipos, d) ->
            ({model | query = doCallin model.query cbpos cipos (iSetCallin (\v -> d))
                ,disallowSelectionList = deselectQueryResults model.disallowSelectionList
            },Cmd.none)
        SetParsedCallback(cbpos,d) ->
            ({model | query = doCallback (\v -> d) model.query cbpos
                ,disallowSelectionList = deselectQueryResults model.disallowSelectionList
            }, Cmd.none)
        GetParsedCallback(cbpos, oldcbdat) -> (model, parseCallback cbpos oldcbdat)
        GetParsedCallin(cbpos, cipos, oldcidat) -> (model, parseCallin cbpos cipos oldcidat)
        SetCallbackInput(cbpos, s) ->
            ({model | query = doCallback (\v -> {v | input = s, parsed = NotParsed(model.ctime)}) model.query cbpos
                ,disallowSelectionList = deselectQueryResults model.disallowSelectionList}, Cmd.none)
        SetCallinInput(cbpos, cipos, s) ->
            ({model |
                query = doCallin model.query cbpos cipos (iSetCallin (\v -> {v | input = s, parsed = NotParsed(model.ctime)}))
                ,disallowSelectionList = deselectQueryResults model.disallowSelectionList
            },Cmd.none)
        SearchCallinHole (cbpos, cipos) -> (model, searchCallinHole cbpos cipos model.query)
        UnSetParsedCallback (cbpos) ->
            ({model | query = doCallback (\v -> {v | parsed = ParseError}) model.query cbpos}, Cmd.none)
        UnSetParsedCallin (cbpos, cipos) ->
            ({model | query = doCallin model.query cbpos cipos (iSetCallin (\v -> {v | parsed = ParseError}))}, Cmd.none)
        SetCallinHoleResults(cbpos,cipos, resList) ->
            ({model | query = doCallinHole model.query cbpos cipos resList}, Cmd.none)
        DisplayCallbackError(cbpos, string) -> (model,Cmd.none) --TODO
        DisplayCallinError(cbpos, cipos, string) ->
            (model, Cmd.none) -- TODO
        SetQueryList(l) -> ({model | querySelectionList = l},Cmd.none)
        SetDisallowList(l) -> (
            {model | disallowSelectionList =
                Dict.fromList (List.map (\a -> (a,VerificationNoResults)) l)
            }, Cmd.none)
        GetQueryList -> (model, getQueryList)
        GetDisallowList -> (model, getDisallowList)
        QuerySelectDropToggle t -> ({model | querySelectDropDownState = t}, Cmd.none)
        SetQuerySelection name -> ({model | disallowSelectionList = deselectQueryResults model.disallowSelectionList}
            , Cmd.batch [getQuery name, getQueryDescription name])
        SetQuery q -> ({model | query = q}, Cmd.none)
        GetVerificationResults(name, id) -> (model, getVerificationResults model.query id name)
        SetVerificationResults (name, r) ->
            ({model | disallowSelectionList = Dict.insert name r model.disallowSelectionList}, Cmd.none)
        PostVerificationTask (r) ->
            (model, postVerificationTask model.query r)
        Nop -> (model,Cmd.none)
        SelectResultsTab (r) -> ({model | resultsTabSelected = r}, Cmd.none)
        ParseAll(t) -> ({model| ctime = t}, parseAll t model.query)
        IncrCxe -> ({model | resultsTabSelected = incrCxe model.resultsTabSelected} , Cmd.none)
        DecrCxe -> ({model | resultsTabSelected = decrCxe model.resultsTabSelected}, Cmd.none)
        SetQueryDescription(description) -> ({model | queryDescription= description} , Cmd.none)
        GetQueryDescription(qname) -> (model, getQueryDescription qname)

deselectQueryResults : (Dict.Dict String VerificationResults) -> (Dict.Dict String VerificationResults)
deselectQueryResults vr =
    Dict.map (\prop -> \old -> VerificationNoResults) vr


iDoCallinHole : List QueryCommand -> Int -> List RankedMessage -> List QueryCommand
iDoCallinHole olist cipos res =
    List.indexedMap (\idx -> \v ->
        (case (idx, v) of
            (cipos, QueryCommandHole) -> QueryCommandHoleResults(res)
            (a,b) -> b
        )) olist

doCallinHole : List QueryCallbackOrHole -> Int -> Int -> List RankedMessage -> List QueryCallbackOrHole
doCallinHole olist cbpos cipos res =
    List.indexedMap (\idx -> \v ->
        ( case (idx, v) of
            (cbpos, QueryCallback(d)) -> QueryCallback({d | commands = iDoCallinHole d.commands cipos res})
            (a,b) -> b --TODO: callins within callback holes
        )) olist

-- View

inputBox : QueryCallbackData -> Input.Option msg -> List (Input.Option msg)
inputBox d upd=
    case (d.parsed, d.input) of
        (NotParsed _,"") -> [ Input.attrs [ Spacing.ml2 ], Input.placeholder "--input method query--", upd]
        (NotParsed _, s) -> [ Input.attrs [ Spacing.ml2 ], Input.value s, upd ]
        (Parsed, s) -> [ Input.attrs [ Spacing.ml2 ], Input.value s, upd ]
        (ParseError, s) -> [ Input.attrs [ Spacing.ml2 ], Input.value s, upd]
ciInputBox : QueryCallinData -> Input.Option msg -> List (Input.Option msg)
ciInputBox d upd=
    case (d.parsed, d.input) of
        (NotParsed _,"") -> [ Input.placeholder "--input method query--", upd]
        (NotParsed _, s) -> [ Input.value s, upd ]
        (Parsed, s) -> [ Input.value s, upd ]
        (ParseError, s) -> [ Input.attrs [ Spacing.ml2 ], Input.value s, upd]
columnCard contents =
    Card.config [  ] |> Card.block [] contents |> Card.view


queryEntry model =
    div [] [
            Dropdown.dropdown model.querySelectDropDownState
                {options = [ Dropdown.attrs [Spacing.ml1] ]
                , toggleMsg = QuerySelectDropToggle
                , toggleButton =
                    Dropdown.toggle [ Button.primary ] [ text "Trace Template" ]
                , items = List.map (\name -> Dropdown.buttonItem [ Html.Events.onClick <|
                    (SetQuerySelection name) ] [text name] ) model.querySelectionList
                } -- , GetQueryDescription name] --TODO: chain these together
            ]

verifyTab model =
    case model.resultsTabSelected of
        ResultsVerify _ -> Button.primary
        ResultsSearch -> Button.secondary

searchTab model =
    case model.resultsTabSelected of
        ResultsSearch -> Button.primary
        ResultsVerify _ -> Button.secondary

resultsView model =
     div [] [
--        Button.button [Button.attrs [ Spacing.ml1]
--            , verifyTab model, Button.onClick (SelectResultsTab (ResultsVerify Nothing))] [ text "Verify" ]
--        , Button.button [Button.attrs [ Spacing.ml1]
--            , searchTab model, Button.onClick (SelectResultsTab ResultsSearch)] [ text "Search" ]
        ]

ciholeButtons : Int -> Int -> Html Msg
ciholeButtons cbpos cipos =
    div [] [
        Button.button
            [Button.attrs [ Spacing.ml1], Button.small, Button.onClick (FillQueryCallinhole(cbpos,cipos))]
            [ text "*" ]
        , Button.button
            [Button.attrs [ Spacing.ml1], Button.small, Button.onClick (SearchCallinHole(cbpos,cipos))] [text "?"]]


displayQueryResults : Int -> Int -> Int -> String -> List RankedMessage -> Html Msg
displayQueryResults cbpos cipos limit filter results =
    let
        hightolow : List RankedMessage
        hightolow = List.reverse (List.sortBy .rank results)
        firstn : List RankedMessage
        firstn = List.take limit hightolow
        rank_string_list : List (String,String)
        rank_string_list = List.map (\a -> ((toString a.rank) , (rankedMessageToInput a))  ) firstn
    in
        ListGroup.custom
            (List.map
               (\a -> ListGroup.button [ListGroup.success, ListGroup.attrs [onClick (SetCallinInput (cbpos, cipos, Tuple.second a))] ] [ text ((Tuple.first a) ++ (Tuple.second a)) ])
               rank_string_list)



isperr : ParseStatus -> List (Html Msg)
isperr a =
    case a of
        ParseError -> [ Badge.badgeDanger [] [text "Er"] ]
        NotParsed(_) -> [ Badge.badgeSecondary [] [text "In"] ]
        _ -> [ Badge.badgeSuccess [] [text "Ok"] ]

callinView : Int -> Int -> QueryCommand -> Html Msg
callinView cbpos cipos callin =
    let
        (contents, displayerr) =
            case callin of
                QueryCallin c -> ((Input.text
                    ((Input.attrs [Attributes.attribute "class" "ci-entry"])
                        ::(ciInputBox c (Input.onInput (\s -> SetCallinInput (cbpos, cipos, s)))))), isperr c.parsed)
                QueryCommandHole -> (ciholeButtons cbpos cipos, [])
                QueryCommandHoleResults(l) -> (displayQueryResults cbpos cipos 20 "" l, [])
        buttons = [Button.button
                      [Button.attrs [ Spacing.ml1], Button.small, Button.onClick (RemoveQueryCallin(cbpos,cipos)) ]
                      [text "x"]
                  , Button.button
                      [Button.attrs [Spacing.ml1], Button.small, Button.onClick (AddQueryCallinAfter(cbpos,cipos)) ]
                      [text "v"] ]
--        displayerr =
--            case callin.parsed of
--                ParseError -> True
--                _ -> False
    in
        Grid.container[] [Grid.row [ ] [Grid.col [Col.middleXl] [contents], Grid.col [Col.sm3] [
            div [Attributes.attribute "class" "ci-buttons"] (displayerr ++ buttons)] ] ]
--            div [] (if displayerr then (div [Attributes.attribute "class" "div-red"] [text "E"]) :: buttons else buttons) ]] ]


callbackView : Int -> QueryCallbackOrHole -> Html Msg
callbackView cbpos callback =
    let
        (contents, displayerr) =
            case callback of
                QueryCallback(d) -> (Input.text ((Input.attrs [Attributes.attribute "class" "cb-entry"])::(inputBox d
                    (Input.onInput (\s -> SetCallbackInput(cbpos, s)))
                    )), isperr d.parsed)
                QueryCallbackHole ->
                    (div [] [Button.button [Button.attrs [Spacing.ml1], Button.small, Button.onClick (FillQueryCallbackHole cbpos)] [text "*"],
                        Button.button [ Button.attrs [Spacing.ml1], Button.small ] [text "?"] ], []) --TODO: search click
                QueryCallbackHoleResults(r) -> (text "TODO", []) -- TODO: display search results
        callins =
            case callback of
                QueryCallback(d) -> [ Grid.row [] [
                    Grid.col [] [
                        ListGroup.ul (List.indexedMap
                            (\idx -> \a -> ListGroup.li [ListGroup.warning] [(callinView cbpos idx a)])
                            d.commands)] ] ]
                _ -> []
    in
--        Grid.container [Attributes.attribute "class" displayerr] ([
        Grid.container [] ([
            Grid.row [] [
                Grid.col [] [ contents ]
                ,Grid.col [Col.sm4] [
                    div [Attributes.attribute "class" "cb-buttons"] (
                    displayerr ++
                    [Button.button [Button.attrs [ Spacing.ml1], Button.small, Button.onClick (RemoveQueryCallback cbpos) ] [text "x"]
                    ,Button.button [Button.attrs [ Spacing.ml1 ], Button.small, Button.onClick (AddQueryCallinAfter (cbpos, -1))] [ text "<" ]
                    ,Button.button [Button.attrs [ Spacing.ml1], Button.small, Button.onClick (AddQueryCallbackAfter cbpos)] [text "v"]
                    ] )
                ] ] ] ++ callins)

verifRunningDisp : Int -> Model -> String -> Html Msg
verifRunningDisp idx model name =
    case Dict.get name model.disallowSelectionList of
        Just VerificationNoResults -> (Button.button
            [Button.small, Button.onClick (SelectResultsTab (ResultsVerify (Just idx))), Button.primary ]
            [text "Not Run"])
        Just (VerificationPending _ ) -> (Button.button
            [Button.small, Button.onClick (SelectResultsTab (ResultsVerify (Just idx))), Button.secondary]
            [text "Running"])
        Just (VerificationUnsafe _ ) -> (Button.button
            [Button.small, Button.onClick (SelectResultsTab (ResultsVerify (Just idx))), Button.danger]
            [text "Unsafe Trace"])
        Just VerificationSafe -> (Button.button
            [Button.small, Button.onClick (SelectResultsTab (ResultsVerify (Just idx))), Button.success]
            [text "Safe Trace"])
        Just (VerificationError(string)) -> (Button.button
            [Button.small, Button.onClick (SelectResultsTab (ResultsVerify (Just idx))), Button.warning]
            [text "Internal Error"])
        _ -> text ""


displayCounterExample : List QueryCallbackOrHole -> Html Msg
displayCounterExample qc =
    let
        cidisp = \c ->
            case c of
                QueryCallin (cidat) ->
                    ListGroup.li [] [text cidat.input]
                _ -> Debug.crash ""
        cbdisp = \a ->
            case a of
                QueryCallback(cbdat) ->
                    ListGroup.li [] [
                        Grid.container [] [
                            Grid.row [] [
                                Grid.col [] [text cbdat.input]]
                            ,Grid.row [] [ Grid.col [] [ListGroup.ul (List.map cidisp cbdat.commands) ]]
                        ]
                    ]
                _ -> Debug.crash ""
    in
        ListGroup.ul (List.map cbdisp qc)

displayVerificationResult : Maybe VerificationResults -> String -> Html Msg
displayVerificationResult v rule =
    case v of
        Just (VerificationError m) -> text m
        Just VerificationSafe -> text ("Trace is safe for " ++ rule ++ ".")
        Just (VerificationUnsafe c) -> Grid.container [] [Grid.row [] [ Grid.col [] [text ("Trace is unsafe for " ++ rule ++ ", counter example:")]]
                , Grid.row [] [Grid.col [] [displayCounterExample c] ]
            ]
        Just (VerificationPending _) -> text ("Results are pending for " ++ rule ++ ".")
        Just VerificationNoResults -> text ("Please select the checkbox for " ++ rule ++ " to run.")
        Nothing -> text ""

nameFromRulePos : Int -> Model -> String
nameFromRulePos p model =
    let
        keys = Dict.keys model.disallowSelectionList
     in
        case List.head (List.drop p keys) of
            Just v -> v
            _ -> ""

verifyView : Maybe Int -> Model -> Html Msg
verifyView s model =
    let
        selectedName =
            case s of
                Nothing -> "lakjsdflkahsdfjhasdfkjhasdkjfhasdkfjh"
                Just v -> nameFromRulePos v model
        incrEnabled =
            case s of
                Nothing -> Button.disabled False
                Just (sz) -> Button.disabled (Dict.size model.disallowSelectionList == (sz-2))
        decrEnabled =
            case s of
                Nothing -> Button.disabled True
                Just (sz) -> Button.disabled (sz == 0)
        cxe_display =
            case s of
                Nothing -> div [] []
                Just v ->
                    let
                        n = nameFromRulePos v model
                    in
                        displayVerificationResult (Dict.get n model.disallowSelectionList) n
        b_attr = [Button.attrs [Spacing.ml1], Button.primary, Button.small]
    in
        Grid.container [] [
            Grid.row [] [
                Grid.col [] [
                    ListGroup.ul (
                        List.indexedMap
                            (\idx -> \a ->
                                let
                                    dis =
                                        case Dict.get a model.disallowSelectionList of
                                            Nothing -> True
                                            Just VerificationNoResults -> False
                                            _ -> True
                                in
                                    ListGroup.li [] [Grid.container [] [
                                        Grid.row [] [Grid.col [Col.sm1] [ if selectedName == a then (Badge.badgeDark [] [text "Sel"]) else (text "")]
                                            ,Grid.col [Col.sm2] [ Button.button [Button.onClick (PostVerificationTask a), Button.disabled dis, Button.primary, Button.small] [text "Verify"] ]
                                            ,Grid.col [Col.sm4] [text (String.join ". " (String.split "." a))]
                                            ,Grid.col [] [(verifRunningDisp idx model a) ] ] ] ] )
                            (Dict.keys model.disallowSelectionList) )
                ]
            ]
            , Grid.row [] [Grid.col [] [text " "]]
            , Grid.row [] [Grid.col [] [div [] [
--                Button.button ((Button.onClick DecrCxe) :: decrEnabled :: b_attr) [text "<"] --Note: these are buttons to toggle displayed result
--                , Button.button ((Button.onClick IncrCxe) :: incrEnabled :: b_attr) [text ">"]
            ] ]]
            , Grid.row [] [
                Grid.col [] [cxe_display]
            ]
        ]

searchView : Model -> Html Msg
searchView model = div [] [text "search view"]

view : Model -> Html Msg
view model =
    Grid.container []
        [ Grid.row []
            [ Grid.col [ Col.orderXlFirst] [ columnCard [ Block.custom (queryEntry model)
                , Block.text [] [ text model.queryDescription ]
                , Block.custom (
                    ListGroup.ul (List.indexedMap (\idx -> \a -> ListGroup.li [ ListGroup.dark ] [callbackView idx a]) model.query )
                )]
                ]
            , Grid.col [ Col.orderXlLast ] [ columnCard [ Block.custom (resultsView model)
                , Block.custom (
                    case model.resultsTabSelected of
                        ResultsVerify s -> verifyView s model
                        ResultsSearch -> searchView model
                ) ]
                ]
            ]
        ]




-- SUBSCRIPTIONS

pendingVerifications : Dict.Dict String VerificationResults -> List (String,Int)
pendingVerifications verificationResults =
    let
        dmap = Dict.toList
            (Dict.filter (\key -> \v ->
                    case v of
                        VerificationPending(i) -> True
                        _ -> False
                )
                verificationResults)
    in
        List.map (\a ->
            case a of
                (name, VerificationPending(i)) -> (name,i)
                _ -> Debug.crash "..."
        ) dmap

subscriptions : Model -> Sub Msg
subscriptions model =
    Sub.batch
        (
            (Dropdown.subscriptions model.querySelectDropDownState QuerySelectDropToggle)
            ::
            (Time.every (3 * Time.second) ParseAll)
            ::
            (List.map (\nid ->(
                    Time.every
                        (5 * Time.second)  --TODO: increase time here
                        (\time ->
                                GetVerificationResults(Tuple.first nid, Tuple.second nid)) ))
                    (pendingVerifications model.disallowSelectionList))
        )

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
                                                        , parsed = Parsed
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
                                                          , parsed = Parsed
                                                          , params = List.map qAsQueryParam v.parameters })
                Qt.MProblem(p) -> UnSetParsedCallback(cbpos)
                Qt.MCallin(v) -> UnSetParsedCallback(cbpos)
                Qt.MsgUnspecified -> UnSetParsedCallback(cbpos)

        Err(v) -> UnSetParsedCallback(cbpos) --TODO: display error

setCallinHoleResults : Int -> Int -> Result Http.Error (List RankedCallinProto) -> Msg
setCallinHoleResults cbpos cipos result =
    case result of
        Ok(result) -> SetCallinHoleResults(cbpos, cipos, List.map rankedCallinProtoToQuery result)
        Err(v) -> DisplayCallinError(cbpos, cipos, "http error") -- TODO: display error

setQueryList : Result Http.Error (List String) -> Msg
setQueryList result =
    case result of
        Ok(lst) -> SetQueryList(lst)
        Err(v) -> Debug.crash "display setQueryList get error" SetQueryList([]) --TODO: display better error than empty list

setDisallowList : Result Http.Error (List String) -> Msg
setDisallowList result =
    case result of
        Ok(lst) -> SetDisallowList(lst)
        Err(v) -> SetDisallowList([])

setQuery : Result Http.Error Qt.CTrace -> Msg
setQuery result =
    case result of
        Ok(ctr) -> SetQuery(cTraceAsQuery ctr)
        Err(v) -> SetQuery([]) -- TODO: display error

getQueryList : Cmd Msg
getQueryList =
    Http.send setQueryList <| Http.get "/query_list" (Decode.list Decode.string)

getDisallowList : Cmd Msg
getDisallowList =
    Http.send setDisallowList <| Http.get "/get_disallow_list" (Decode.list Decode.string)



getQuery : String -> Cmd Msg
getQuery name =
    Http.send setQuery <| Http.get ("/get_query/" ++ name) Qt.cTraceDecoder

type alias RankedCallinProto =
    {
        rank : Int
        , callin : Qt.CCallin
    }
rankedCallinProtoToQuery : RankedCallinProto -> RankedMessage
rankedCallinProtoToQuery r =
    {rank = r.rank, msg = MessageResponseCi (cCallinAsQuery r.callin)}

--type alias RespVerificationResults =
--    {
--        status : String,
--        msg : String,
--        cxe : Qt.CTrace
--    }

setVerificationResults : String -> Result Http.Error Qt.VerificationResult -> Msg
setVerificationResults name c =
    let
        _ = 1
--        _ = Debug.log "name is : " name
--        _ = Debug.log "ctr is : " c
    in
        case c of
            Ok(ctr) ->
                case (ctr.status, ctr.msg, ctr.counterExample) of
                    ("SAFE",_,_) -> SetVerificationResults (name, VerificationSafe)
                    ("UNSAFE", _, Just cxe) -> SetVerificationResults (name, VerificationUnsafe( cTraceAsQuery cxe))
                    ("ERROR", er, _) -> SetVerificationResults (name, VerificationError (er))
                    ("RUNNING", _, _) -> Nop
                    (_,_,_) -> SetVerificationResults (name, VerificationError ("Corrupted server response."))
            Err(v) -> SetVerificationResults(name, VerificationError(toString v))

setVerificationTaskId : String -> Result Http.Error Int -> Msg
setVerificationTaskId name c =
    case c of
        Ok(id) -> SetVerificationResults(name, VerificationPending( id))
        Err(v) -> SetVerificationResults(name, VerificationError(toString v))


--decodeVerificationResults : Decode.Decoder RespVerificationResults
--decodeVerificationResults =
--    Decode.map3 RespVerificationResults
--        (Decode.field "status" Decode.string)
--        (Decode.field "msg" Decode.string)
--        (Decode.field "counter_example" Qt.cTraceDecoder)

--    Decode.succeed RespVerificationResults
--        |> Pipeline.required "status" Decode.string
--        |> Pipeline.optional "msg" Decode.string ""
--        |> Pipeline.optional "counter_example" Qt.cTraceDecoder {id = Nothing, callbacks = []} --TODO: this is not decoding, WHY!!!???


postVerificationTask : List QueryCallbackOrHole -> String -> Cmd Msg
postVerificationTask q rule =
    Http.send (setVerificationTaskId rule)
        (reqHdr ("/verify?rule=" ++ rule)
            (Http.jsonBody <| Qt.cTraceEncoder <| queryAsQ Nothing Nothing q)
            (Decode.field "id" Decode.int))


getVerificationResults : List QueryCallbackOrHole -> Int -> String -> Cmd Msg
getVerificationResults q id name=
    Http.send (setVerificationResults name)
        (Http.get ("/status?id=" ++ (toString id))
            Qt.verificationResultDecoder)

setQueryDescription : Result Http.Error String -> Msg
setQueryDescription r =
    case r of
        Ok(r) -> SetQueryDescription(r)
        Err(v) -> SetQueryDescription("An error occurred while retrieving the documentation.")

getQueryDescription : String -> Cmd Msg
getQueryDescription name =
    Http.send setQueryDescription
        (Http.getString ("/get_query_doc/" ++ name))
--        (Decode.field "doc" Decode.string)


searchCallinHole : Int -> Int -> List QueryCallbackOrHole -> Cmd Msg
searchCallinHole cbpos cipos model =
        Http.send (setCallinHoleResults cbpos cipos)
            (reqHdr "/completion_search"
                (Http.jsonBody <| Qt.cTraceEncoder <| queryAsQ (Just cbpos) (Just cipos) model)
                (Decode.list
                    (Decode.map2 RankedCallinProto
                        (Decode.field "rank" Decode.int)
                        (Decode.field "callin" Qt.cCallinDecoder))))


readyToParse :Float -> ParseStatus -> Bool
readyToParse ctime s =
    case s of
        Parsed -> False
        ParseError -> False -- Don't reparse until text is changed
        NotParsed(t) -> (ctime - t) > (Time.second * 3)

recParseCallin : Time -> Int -> Int -> QueryCommand -> Maybe (Cmd Msg)
recParseCallin ctime cbpos cipos c =
    case c of
        QueryCallin(d) -> if readyToParse ctime d.parsed then (Just (parseCallin cbpos cipos d)) else Nothing
        _ -> Nothing

recParseCallback : Float -> Int -> QueryCallbackOrHole -> Cmd Msg
recParseCallback ctime cbpos cbh =
    case cbh of
        QueryCallback(d) ->
            let
                subcommands =  List.filterMap (\a -> a) (List.indexedMap (recParseCallin ctime cbpos) d.commands)
            in
                Cmd.batch (if readyToParse ctime d.parsed then parseCallback cbpos d :: subcommands else subcommands )
        _ -> Cmd.batch []

parseAll: Float -> List QueryCallbackOrHole -> Cmd Msg
parseAll ctime query =
    Cmd.batch (List.indexedMap (recParseCallback ctime) query)

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
        BooleanPrimitive(b) -> if b then "TRUE" else "FALSE"
        IntegerPrimitive(i) -> toString i
        LongPrimitive(i) -> toString i
        StringPrimitive(s) -> s
        Hole -> "#"

queryFrameworkClassToInput : List Param -> String -> String
queryFrameworkClassToInput params fmwk =
    let
        parstrings = List.map queryParamToInput params
        parsplit = String.split "(" fmwk
    in
        case parsplit of --TODO: bug here when no params
            front :: paramtypes :: t ->
                let
                    zpars = List.map2 (\pstr -> \ptyp -> pstr ++ " : " ++ ptyp) parstrings (String.split "," paramtypes)
                    pjoin = String.join " , " zpars
                in
                    case zpars of
                        h :: t -> front ++ ("(" ++ pjoin) -- ++ "   DBG: " ++ (List.head (String.split "," paramtypes))
                        _ -> front ++ ("()")
            nil -> "error"

rankedMessageToInput : RankedMessage -> String
rankedMessageToInput msg =
    case msg.msg of
        MessageResponseCi(d) -> queryCallinDataToInput d
        MessageResponseCb(d) -> queryCallbackDataToInput d

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
                        , parsed = Parsed
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


cCallinAsQuery : Qt.CCallin -> QueryCallinData
cCallinAsQuery v =
    let
        d = {frameworkClass = v.frameworkClass
            , signature = v.methodSignature
            , input = "auto fill"
            , parsed = Parsed
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
        Qt.Primitive(prim) -> qAsQueryPrimitive prim.primitive
        _ -> Hole

qAsQueryPrimitive : Qt.Primitive -> Param
qAsQueryPrimitive qprim =
    case qprim of
        Qt.PrimitiveUnspecified -> Hole
        Qt.BoolVal(v) -> BooleanPrimitive(v)
        Qt.IntVal(v) -> IntegerPrimitive(v)
        Qt.LongVal(v) -> LongPrimitive(v)
        Qt.StringVal(v) -> StringPrimitive(v)



-- Serialization

queryParamAsQ : Param -> Qt.CParam
queryParamAsQ p =
    let
        primize = \a -> {param = Qt.Primitive ({primitive = a} )}
    in
        case p of
            NamedVar(s) -> {param = Qt.Variable ({name = s}) }
            BooleanPrimitive(b) -> primize (Qt.BoolVal b)
            IntegerPrimitive(i) -> primize (Qt.IntVal i)
            LongPrimitive(l) -> primize (Qt.LongVal l)
            StringPrimitive(s) -> primize (Qt.StringVal s)
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