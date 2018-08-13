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
        receiver : Param
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

init : ( Model, Cmd Msg)
init =
    ( Model [QueryCallbackHole], Cmd.none)


-- UPDATE

addHole old pos =
    case (old,pos) of
        (h :: old, 0) -> h :: QueryCallbackHole :: old
        (h :: t, a) -> h :: addHole t (a-1)
        (nil, a) -> nil

type Msg
    = AddQueryCallbackAfter (Int)
    | AddQueryCallinAfter (Int, Int)
    | FillQueryCallbackHole (Int)
    | FillQueryCallinhole (Int,Int)
update : Msg -> Model -> ( Model, Cmd Msg )
update msg model =
    case msg of
        AddQueryCallinAfter (callbackPos, callinPos) -> (model, Cmd.none) -- TODO
        AddQueryCallbackAfter(callbackPos) -> ({model | query = addHole model.query callbackPos}, Cmd.none) -- TODO
        FillQueryCallbackHole(callbackPos) -> (model, Cmd.none) -- TODO
        FillQueryCallinhole(callbackPos, callinPos) -> (model, Cmd.none) --TODO


-- View

holeCard pos =
    Card.block []
                [ Block.titleH4 [] [ text "Hole" ]
                , Block.text [] [ text (toString pos) ]
                , Block.custom <|
                    Button.button [ Button.primary, Button.onClick (AddQueryCallbackAfter pos)] [ text "+" ] --
                , Block.custom (text " ")
                , Block.custom <|
                    Button.button [ Button.primary ] [ text "-" ]
                , Block.custom (text " ")
                , Block.custom <|
                    Button.button [ Button.secondary ] [ text "Fill" ]

                ]

callbackCard c pos =
    Card.block []
                [ Block.titleH4 [] [ text "Card title" ]
                , Block.text [] [ text "Some quick example text to build on the card title and make up the bulk of the card's content." ]
                , Block.custom <|
                    Button.button   [ Button.primary  ] [ text "+" ]

                ]

callbackOhrHoleCard contents =
    Card.config [ Card.attrs [ style [ ( "width", "20rem" ) ] ] ]
        |> Card.header [ class "text-center" ]
            [ h3 [ ] [ text "" ]
            ]
        |> contents
        |> Card.view

drawCallbackOrHole pos c =
    case c of
        QueryCallback(d) -> callbackOhrHoleCard (callbackCard c pos)
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