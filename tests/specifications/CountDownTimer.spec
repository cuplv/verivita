{
    "specs": [
        {
	    "match": {
                "event": {
		    "concreteArgsVariables": ["counter"],
		    "signature": "CountDownTimer.Finish"
		}
	    },
	    "change": {
                "event": {
		    "concreteArgsVariables": ["counter"],
		    "signature": "CountDownTimer.Finish"
		}                
	    },
	    "type": "disable"
	},
        {
	    "match": {
                "callin": {
		    "concreteArgsVariables": ["counter"],
		    "signature": "CountDownTimer.start"
		}
	    },
	    "change": {
                "event": {
		    "concreteArgsVariables": ["counter"],
		    "signature": "CountDownTimer.Finish"
		}                
	    },
	    "type": "enable"
	},
        {
	    "match": {
                "callin": {
		    "concreteArgsVariables": ["counter"],
		    "signature": "CountDownTimer.cancel"
		}
	    },
	    "change": {
                "event": {
		    "concreteArgsVariables": ["counter"],
		    "signature": "CountDownTimer.Finish"
		}                
	    },
	    "type": "disable"
	}   
    ],
    "bindings" : [
        {
            "event" : {
                "signature" : "CountDownTimer.Finish",
                "concreteArgsVariables" : ["counter"]
            },
            "callback" : {
                "signature" : "CountDownTimer.OnFinish",
                "concreteArgsVariables" : ["counter"]
            }
        }
    ],
    "mappings" : [
        {
            "value" : "class android.os.CountDownTimer (no class loader).start()Landroid/os/CountDownTimer;",
            "name" : "CountDownTimer.start"
        },
        {
            "value" : "class android.os.CountDownTimer (no class loader).cancel()V",
            "name" : "CountDownTimer.cancel"
        },
        {
            "value" : "class android.os.CountDownTimer (no class loader).onFinish()V",
            "name" : "CountDownTimer.OnFinish"
        },
        {
            "value" : "{\"what\":1,\"callbackField\":\"\",\"targetField\":\"class android.os.CountDownTimer$1 (no class loader)\"}",
            "name" : "CountDownTimer.Finish"
        }
    ]
}

    
