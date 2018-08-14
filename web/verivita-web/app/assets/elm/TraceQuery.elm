module TraceQuery exposing (..)

import Html exposing (..)
import Html.Events exposing (onClick)
import Http
import Json.Decode as Json
import Html.Events exposing (onInput)

import Bootstrap.CDN as CDN
import Bootstrap.Grid as Grid
import Bootstrap.Card as Card
import Html.Attributes exposing (class, src, style)
import Bootstrap.Card.Block as Block
import Bootstrap.Button as Button
import Bootstrap.ListGroup as ListGroup
import Bootstrap.Form as Form
import Bootstrap.Form.Input as Input


main : Program Never Model Msg
main =
    program
        {init = init
        , view = view
        , update = update
        , subscriptions = subscriptions}

-- Model

type Param
    = SelectedHole
    | NamedVar(String)
    | Hole


type QueryCallbackOrHole = QueryCallback(QueryCallbackData)
    | QueryCallbackHole
type alias QueryCallbackData =
    {
        frameworkClass : String,
        signature : String,
        receiver : Param,
        commands : List QueryCommand
    }

type QueryCommand
    = QueryCallin(QueryCallinData)
    | QueryCommandHole
type alias QueryCallinData =
    {
        frameworkClass: String,
        signature : String,
        receiver : Param,
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

type alias Model =
    {
        query : List QueryCallbackOrHole
    }
emptyCallback =
    QueryCallback( { frameworkClass = "", signature = "", receiver = Hole, commands = []})
emptyCallin =
    QueryCallin({ frameworkClass = "", signature = "", receiver = Hole , return = Hole})

init : ( Model, Cmd Msg)
init =
    ( Model [QueryCallbackHole], Cmd.none)


-- UPDATE

iAddCallin old cipos =
    case (old,cipos) of
        (t, -1) -> QueryCommandHole :: t
        (h :: t , 0) -> h :: QueryCommandHole :: t
        (nil , 0) -> QueryCommandHole :: nil
        (h :: t, a) -> h :: (iAddCallin t (a - 1))
        (nil , a) -> nil -- TODO: error state

iRemoveCallin old cipos =
    case (old,cipos) of
        (h :: t, 0) -> t
        (h :: t, a) -> h :: (iRemoveCallin t (cipos - 1))
        (nil,a) -> nil -- TODO: error state

iFill old cipos =
    case (old,cipos) of
        (h :: t, 0) -> emptyCallin :: t
        (h :: t, a) -> h :: iFill t (a - 1)
        (nil,a) -> nil -- TODO: error state


doCallin old cbpos cipos fn =
    case (old,cbpos) of
        (QueryCallback(d) :: t, 0) -> (QueryCallback({d | commands = fn d.commands cipos})) :: t
        (h :: t, a) -> h :: (doCallin t (cbpos - 1) cipos fn)
        (nil, a) -> nil --TODO: error state

addHole old pos =
    case (old,pos) of
        (h :: old, 0) -> h :: QueryCallbackHole :: old
        (nil, 0) -> QueryCallbackHole :: nil
        (h :: t, a) -> h :: addHole t (a-1)
        (nil, a) -> nil -- TODO: error state
removeCOH old pos =
    case (old,pos) of
        (h :: old, 0) -> old
        (h :: old, a) -> h :: (removeCOH old (a-1))
        (nil,a) -> nil --TODO: error state


fillHole old pos =
    case (old,pos) of
        (QueryCallbackHole :: old , 0) ->
            emptyCallback :: old
        (h :: old, a) -> h :: fillHole old (a-1)
        (nil,a) -> nil --TODO: eror state

callbackSigSet cblist cbpos signature =
    case (cblist,cbpos) of
        (QueryCallback(d) :: t, 0) -> QueryCallback({d | signature = signature}) :: t
        (h :: t, a) -> h :: callbackSigSet t (cbpos - 1) signature
        (nil,a) -> nil --TODO: error state

callbackFmwkSet cblist cbpos framework =
    List.indexedMap (\idx -> \v ->
        if idx == cbpos then
            case v of
                QueryCallback(v) -> QueryCallback ({v | frameworkClass = framework})
                QueryCallbackHole -> QueryCallbackHole -- TODO: error state
        else v
        ) cblist

iSetCallinFmwk framework old pos =
    case (old,pos) of
        (QueryCallin(v) :: t, 0) -> QueryCallin({v | frameworkClass = framework}) :: t
        (h :: t, a) -> h :: (iSetCallinFmwk framework t (pos - 1))
        (nil, a) -> nil -- TODO: error state
iSetCallinSig sig old pos =
    case (old,pos) of
        (QueryCallin(v) :: t, 0) -> QueryCallin({v | signature = sig}) :: t
        (h :: t, a) -> h :: (iSetCallinSig sig t (pos-1))
        (nil, a) -> nil


type Msg
    = AddQueryCallbackAfter (Int)
    | AddQueryCallinAfter (Int, Int)
    | FillQueryCallbackHole (Int)
    | FillQueryCallinhole (Int,Int)
    | RemoveQueryCallback (Int)
    | RemoveQueryCallin (Int,Int)
    | SetQueryCallbackSig (Int, String)
    | SetQueryCallbackFmwk (Int,String)
    | SetQueryCallinSig (Int,Int, String)
    | SetQueryCallinFmwk (Int,Int, String)
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
        SetQueryCallbackSig (cbpos, signature) ->
            ({model | query = callbackSigSet model.query cbpos signature}, Cmd.none)
        SetQueryCallbackFmwk (cbpos, framework) ->
            ({model |query = callbackFmwkSet model.query cbpos framework}, Cmd.none)
        SetQueryCallinSig (cbpos, cipos, sig) ->
            ({model | query = doCallin model.query cbpos cipos (iSetCallinSig sig)},Cmd.none)
        SetQueryCallinFmwk  (cbpos, cipos, framework) ->
            ({model | query = doCallin model.query cbpos cipos (iSetCallinFmwk framework)},Cmd.none)

-- View

sp =
    Block.custom (text " ")
newline =
    Block.custom (Html.br [] [])

type CiCb = Callin | Callback



holeCard pos =
    Card.block []
                [ Block.titleH4 [] [ text "Hole" ]
                , Block.text [] [ text (toString pos) ]
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

callbackCard d pos =
    Card.block []
                (
                    [ Block.titleH4 [] [ text "Callback" ]
                        , Block.custom (text "Signature")
                        ,Block.custom <|
                            Input.text [ Input.value d.signature
                                ,Input.onInput (\sig -> SetQueryCallbackSig (pos, sig)) ]
--                        , Block.custom <| Button.button [ Button.primary ] [ text "Set" ]
--                        , newline, sp, newline
                        , Block.custom (text "Framework Object")
                        , Block.custom <|
                            Input.text [ Input.value d.frameworkClass
                                ,Input.onInput <| \fmwk -> SetQueryCallbackFmwk (pos,fmwk) ]
                        , newline, sp, newline
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
callinButtons cbpos cipos =
    Card.block []
        [
            Block.custom <|
                Button.button [ Button.primary, Button.onClick (RemoveQueryCallin (cbpos,cipos)) ] [ text "- callin"]
            ,sp
            ,Block.custom <|
                Button.button [ Button.primary, Button.onClick (AddQueryCallinAfter (cbpos,cipos)) ] [ text "+ after"]
            ,sp
            ,Block.custom <|
                Button.button [ Button.secondary, Button.onClick (FillQueryCallinhole (cbpos,cipos)) ] [ text "fill"]
        ]

callinOrHoleAttrs = [ style [ ( "width", "25rem" ) ] ]
callinCard callin cbpos cipos =
        Card.config [ Card.attrs callinOrHoleAttrs ]
            |> Card.header [ class "text-center" ]
                [ h5 [ ] [ text "Callin" ]
                ]
            |> Card.block []
                [
                    Block.custom (text "Signature")
                    , Block.custom <|
                        Input.text [ Input.value callin.signature
                            , Input.onInput (\sig -> SetQueryCallinSig (cbpos, cipos, sig))]
                    , Block.custom (text "Framework Object")
                    , Block.custom <|
                        Input.text [ Input.value callin.frameworkClass
                            , Input.onInput (\fmwk -> SetQueryCallinFmwk (cbpos, cipos, fmwk))]
                ]
            |> callinButtons cbpos cipos
            |> Card.view

callinHoleCard cbpos cipos =
        Card.config [ Card.attrs callinOrHoleAttrs ]
            |> Card.header [ class "text-center" ]
                [ h5 [ ] [ text "Callin Hole" ]
                ]

            |> callinButtons cbpos cipos
            |> Card.view


callinOrHoleCard cbpos cipos c =
    case c of
        QueryCallin(d) -> callinCard d cbpos cipos
        QueryCommandHole -> callinHoleCard cbpos cipos

callbackOhrHoleCard contents =
    Card.config [ Card.attrs [ style [ ( "width", "30rem" ) ] ] ]
        |> Card.header [ class "text-center" ]
            [ h3 [ ] [ text "Callback" ]
            ]
        |> contents
        |> Card.view

drawCallbackOrHole pos c =
    case c of
        QueryCallback(d) -> callbackOhrHoleCard (callbackCard d pos)
        QueryCallbackHole -> callbackOhrHoleCard (holeCard pos)


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