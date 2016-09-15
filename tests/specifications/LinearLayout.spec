{
    "specs": [
	{
	    "change": {
		"callin": {
		    "concreteArgsVariables": [
			"dialogFragment",
			"nn1",
                        "nn2"
		    ],
		    "signature": "DialogFragment.show"
		}
	    },
	    "match": {
		"callin": {
		    "concreteArgsVariables": [
			"dialogFragment",
			"nn3",
                        "nn4"
		    ],
		    "signature": "DialogFragment.show"
		}
	    },
	    "type": "disallow"
	},
	{
	    "change": {
		"callin": {
		    "concreteArgsVariables": [
			"dialogFragment",
			"nn1",
                        "nn2"
		    ],
		    "signature": "DialogFragment:BackStackRecord.remove"
		}
	    },
	    "match": {
		"callin": {
		    "concreteArgsVariables": [
			"dialogFragment",
			"nn3",
                        "nn4"
		    ],
		    "signature": "DialogFragment.show"
		}
	    },
	    "type": "allow"
	}
    ],
    "bindings": [

            ],
    "mappings": [
	{
	    "name": "DialogFragment.show",
	    "value": "class android.support.v4.app.DialogFragment (no class loader).show(Landroid/support/v4/app/FragmentTransaction;Ljava/lang/String;)I"
	},
        {
            "name":"DialogFragment:BackStackRecord.remove",
            "value":"class android.support.v4.app.BackStackRecord (no class loader).remove(Landroid/support/v4/app/Fragment;)Landroid/support/v4/app/FragmentTransaction;"
        }
    ]
}
