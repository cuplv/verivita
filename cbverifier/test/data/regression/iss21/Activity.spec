{
    "specs": [
        {
	    "match": {
		"event": {
		    "concreteArgsVariables": ["fragment"],
		    "signature": "Activity.Create"
		}
	    },
	    "change": {
		"event": {
		    "concreteArgsVariables": ["fragment"],
		    "signature": "Activity.Create"
		}
	    },
	    "type": "disable"
	}        
    ],
    "bindings" : [
        {
            "event" : {
                "signature" : "Activity.Create",
                "concreteArgsVariables" : ["fragment"]
            },
            "callback" : {
                "signature" : "FragmentActivity.OnCreate",
                "concreteArgsVariables" : ["fragment", "nn1"]
            }
        },
        {
            "event" : {
                "signature" : "Activity.Create",
                "concreteArgsVariables" : ["activity"]
            },
            "callback" : {
                "signature" : "ActionBarActivity.OnCreate",
                "concreteArgsVariables" : ["activity", "x"]
            }
        }
    ],
    "mappings" : [
        {
            "value" : "{\"what\":100,\"callbackField\":\"\",\"targetField\":\"class android.app.ActivityThread$H (no class loader)\"}",
            "name" : "Activity.Create"
        },
        {
            "value" : "class android.support.v4.app.FragmentActivity (no class loader).onCreate(Landroid/os/Bundle;)V",
            "name" : "FragmentActivity.OnCreate"
        },
        {
            "value" : "class android.support.v7.app.ActionBarActivity (no class loader).onCreate(Landroid/os/Bundle;)V",
            "name" : "ActionBarActivity.OnCreate"
        }        
    ]
}
