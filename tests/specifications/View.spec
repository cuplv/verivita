{
    "specs": [
        {
	    "match": {
                "event": {
		    "concreteArgsVariables": [
			"view"
		    ],
		    "signature": "View.Detach"
		}
	    },
	    "change": {
		"event": {
		    "concreteArgsVariables": ["view"],
		    "signature": "PerformClick"
		}
	    },
	    "type": "disable"
	}
    ],
    "bindings" : [
        {
            "event" : {
                "signature" : "View.Detach",
                "concreteArgsVariables" : ["view"]
            },
            "callback" : {
                "signature" : "View.OnViewDetachedFromWindow",
                "concreteArgsVariables" : ["listener","view"]
            }
        }
    ],
    "mappings" : [
        {
            "value" : "interface android.view.View$OnAttachStateChangeListener (no class loader).onViewDetachedFromWindow(Landroid/view/View;)V",
            "name" : "View.OnViewDetachedFromWindow"
        }
    ]
}
