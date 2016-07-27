{
    "specs" : [
        {
            "match" : {
                "event" : {
                    "signature" : "A",
                    "concreteArgsVariables" : []
                }
            },
            "change" : {
                "callin" : {
                    "signature" : "c2",
                    "concreteArgsVariables" : []
                }
            },
            "type" : "disallow"
        }
    ],
    "bindings" : [        
        { "event" : {"signature" : "A", "concreteArgsVariables" : []},
          "callback" : {"signature" : "cb1", "concreteArgsVariables" : []}},
        { "event" : {"signature" : "B", "concreteArgsVariables" : []},
          "callback" : {"signature" : "cb2", "concreteArgsVariables" : []}}        
    ]
}




