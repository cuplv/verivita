{
    "specs": [
        {
            "match":{
                "event": {
		    "concreteArgsVariables": [],
		    "signature": "initial"
		}
            },
            "change":{
                "event": {
		    "concreteArgsVariables": [
			"fragment"
		    ],
		    "signature": "Fragment.Detach"
		}
            },
            "type": "disable"
        },
        {
	    "match": {
                "event": {
		    "concreteArgsVariables": [
			"fragment"
		    ],
		    "signature": "Fragment.Detach"
		}
	    },
	    "change": {
		"callin": {
		    "concreteArgsVariables": [
			"fragment",
			"int_param"
		    ],
		    "signature": "Fragment.getString"
		}                
	    },
	    "type": "disallow"
	},
        {
	    "match": {
                "event": {
		    "concreteArgsVariables": [
			"fragment"
		    ],
		    "signature": "Fragment.Detach"
		}
	    },
	    "change": {
		"event": {
		    "concreteArgsVariables": [
			"fragment"
		    ],
		    "signature": "Fragment.Detach"
		}                
	    },
	    "type": "disable"
	},
        {
	    "match": {
                "event": {
		    "concreteArgsVariables": [
			"fragment", "activity"
		    ],
		    "signature": "Fragment.Attach"
		}
	    },
	    "change": {
		"event": {
		    "concreteArgsVariables": [
			"fragment","activity"
		    ],
		    "signature": "Fragment.Attach"
		}                
	    },
	    "type": "disable"
	},
        {
	    "match": {
                "event": {
		    "concreteArgsVariables": [
			"fragment", "activity"
		    ],
		    "signature": "Fragment.Attach"
		}
	    },
	    "change": {
		"event": {
		    "concreteArgsVariables": [
			"fragment"
		    ],
		    "signature": "Fragment.Detach"
		}                
	    },
	    "type": "enable"
	},
        {
	    "match": {
		"event": {
		    "concreteArgsVariables": [
			"fragment"
		    ],
		    "signature": "Fragment.Detach"
		}                
	    },
	    "change": {
                "event": {
		    "concreteArgsVariables": [
			"fragment", "activity"
		    ],
		    "signature": "Fragment.Attach"
		}
	    },            
	    "type": "enable"
	}
    ],
    "bindings" : [
        {
            "event" : {
                "signature" : "Fragment.Attach",
                "concreteArgsVariables" : ["fragment","activity"]
            },
            "callback" : {
                "signature" : "Fragment.OnAttach",
                "concreteArgsVariables" : ["fragment","z"]
            }
        },        
        {
            "event" : {
                "signature" : "Fragment.Detach",
                "concreteArgsVariables" : ["fragment"]
            },
            "callback" : {
                "signature" : "Fragment.OnDetach",
                "concreteArgsVariables" : ["fragment"]
            }
        }

    ],
    "mappings" : [
        {
            "value" : "{\"what\":0,\"callbackField\":\"class android.app.FragmentManagerImpl$1 (no class loader)\",\"targetField\":\"class android.os.Handler (no class loader)\"}",
            "name" :  "Fragment.AttachDetach"
        },
        {
            "value" : "class android.app.Fragment (no class loader).onDetach()V",
            "name" :  "Fragment.OnDetach"
        },
        {
            "value" : "class android.support.v4.app.Fragment (no class loader).onDetach()V",
            "name" :  "Fragment.OnDetach"            
        },
        {
            "value" : "class android.app.Fragment (no class loader).onAttach(Landroid/app/Activity;)V",
            "name" :  "Fragment.OnAttach"
        },
        {
            "value" : "class android.support.v4.app.Fragment (no class loader).onAttach(Landroid/app/Activity;)V",
            "name" :  "Fragment.OnAttach"
        },        
        {
            "value" : "class android.app.Fragment (no class loader).getString(I)Ljava/lang/String;",
            "name" : "Fragment.getString"
        },
        {
            "value" : "class android.support.v4.app.Fragment (no class loader).getString(I)Ljava/lang/String;",
            "name" : "Fragment.getString"
        }        
    ]
}
