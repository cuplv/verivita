{
    "specs" : [
        {
            "match" : {
                "event" : {
                    "signature" : "A",
                    "concreteArgsVariables" : ["x"]
                }
            },
            "change" : {
                "callin" : {
                    "signature" : "c2",
                    "concreteArgsVariables" : ["x"]
                }
            },
            "type" : "disallow"
        }
    ],
    "bindings" : [        
        { "event" : {"signature" : "A", "concreteArgsVariables" : ["x"]},
          "callback" : {"signature" : "cb1", "concreteArgsVariables" : ["x"]}},
        { "event" : {"signature" : "B", "concreteArgsVariables" : ["x"]},
          "callback" : {"signature" : "cb2", "concreteArgsVariables" : ["x"]}}
    ]
}




