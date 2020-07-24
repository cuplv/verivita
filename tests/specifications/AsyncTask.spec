{
    "specs": [
	{
	    "change": {
		"callin": {
		    "concreteArgsVariables": [
			"asyncTask",
			"nn1"
		    ],
		    "signature": "AsyncTask.execute"
		}
	    },
	    "match": {
		"callin": {
		    "concreteArgsVariables": [
			"asyncTask",
			"nn0"
		    ],
		    "signature": "AsyncTask.execute"
		}
	    },
	    "type": "disallow"
	},
	{
	    "match": {
		"callin": {
		    "concreteArgsVariables": ["button", "x"],
		    "signature": "AppCompactButton.setEnabled_false"
		}
	    },
	    "change": {
		"event": {
		    "concreteArgsVariables": [
                        "button"
		    ],
		    "signature": "PerformClick"
		}
	    },
	    "type": "disable"
	}
    ],
    "bindings": [
        {
            "event" : {
                "signature" : "PerformClick",
                "concreteArgsVariables" : ["button"]
            },
            "callback" : {
                "signature" : ".onClick(Landroid/view/View;)V",
                "concreteArgsVariables" : ["listener", "button"]
            }
        },
        {
            "event" : {
                "signature" : "PerformClick",
                "concreteArgsVariables" : ["view"]
            },
            "callback" : {
                "signature" : "View.OnClickListener",
                "concreteArgsVariables" : ["listener", "view"]
            }
        }
    ],
    "mappings": [
	{
	    "name": "AsyncTask.execute",
	    "value": "class android.os.AsyncTask (no class loader).execute([Ljava/lang/Object;)Landroid/os/AsyncTask;"
	},
	{
	    "name": "AppCompact.onCreate",
	    "value": "class android.support.v7.app.AppCompatActivity (no class loader).onCreate(Landroid/os/Bundle;)V"
	},
	{
	    "name": "AppCompact.setContentView",
	    "value": "class android.support.v7.app.AppCompatActivity (no class loader).setContentView(I)V"
	},
	{
	    "name": "AppCompact.findViewById",
	    "value": "class android.support.v7.app.AppCompatActivity (no class loader).findViewById(I)Landroid/view/View;"
	},
	{
	    "name": "AsyncTask.init(TextView)",
	    "value": "class android.os.AsyncTask (no class loader).<init>(Landroid/widget/TextView;)V"
	},
	{
	    "name": "AsyncTask.init",
	    "value": "class android.os.AsyncTask (no class loader).<init>()V"
	},
	{
	    "name": "AppCompactButton.setOnClickListener",
	    "value": "class android.support.v7.widget.AppCompatButton (no class loader).setOnClickListener(Landroid/view/View$OnClickListener;)V"
	},
        {
            "value" : "class android.support.v7.widget.AppCompatButton (no class loader).setEnabled(Z)V",
            "name" : "AppCompactButton.setEnabled"
        },
        {
            "value": "class android.os.AsyncTask (no class loader).onPostExecute(Ljava/lang/Object;)V",
            "name": "android.os.AsyncTask.onPostExecute(obj)"
        },
        {
            "value": "class android.os.AsyncTask (no class loader).onPostExecute(Ljava/lang/String;)V",
            "name": "android.os.AsyncTask.onPostExecute(string)"
        },
        {
            "value": "class android.support.v7.widget.AppCompatTextView (no class loader).setText(Ljava/lang/CharSequence;)V",
            "name": "AppCompatTextView.setText"
        },
        {
            "name" : "AppCompactButton.setEnabled_false",
            "value" : "class android.support.v7.widget.AppCompatButton (no class loader).setEnabled(Z)V_false"
        },
        {
            "value" : ".<init>(Lplv/colorado/edu/asynctasktest/MainActivity;Lplv/colorado/edu/asynctasktest/BackgroundTask;Landroid/widget/Button;)V",
            "name" : ".<init>_anonymous_click"
        },
        {
            "value" : ".onClick(Landroid/view/View;)V",
            "name" : ".onClick(Landroid/view/View;)V"
        },
        {
            "value" : "{\"what\":0,\"callbackField\":\"class android.app.ActivityThread$StopInfo (no class loader)\",\"targetField\":\"class android.app.ActivityThread$H (no class loader)\"}",
            "name" : "{0_android.app.ActivityThread$StopInfo"
        },
        {
            "value" : "{\"what\":0,\"callbackField\":\"class android.support.v7.app.AppCompatDelegateImplV7$1 (no class loader)\",\"targetField\":\"class android.view.ViewRootImpl$ViewRootHandler (no class loader)\"}",
            "name" : "0_AppCompatDelegateImplV7"
        },
        {
            "value" : "{\"what\":0,\"callbackField\":\"class android.view.Choreographer$FrameDisplayEventReceiver (no class loader)\",\"targetField\":\"class android.view.Choreographer$FrameHandler (no class loader)\"}",
            "name" : "0_Choreographer$FrameDisplayEventReceiver"
        },
        {
            "value" : "{\"what\":0,\"callbackField\":\"class android.view.View$PerformClick (no class loader)\",\"targetField\":\"class android.view.ViewRootImpl$ViewRootHandler (no class loader)\"}",
            "name" : "PerformClick"
        },
        {
            "value" : "{\"what\":0,\"callbackField\":\"class android.view.ViewRootImpl$4 (no class loader)\",\"targetField\":\"class android.view.ViewRootImpl$ViewRootHandler (no class loader)\"}",
            "name" : "0_android.view.ViewRootImpl$4"
        },
        {
            "value" : "{\"what\":0,\"callbackField\":\"class android.view.View$UnsetPressedState (no class loader)\",\"targetField\":\"class android.view.ViewRootImpl$ViewRootHandler (no class loader)\"}",
            "name" : "{0_class android.view.View$UnsetPressedState"
        },
        {
            "value" : "{\"what\":100,\"callbackField\":\"\",\"targetField\":\"class com.android.internal.view.IInputConnectionWrapper$MyHandler (no class loader)\"}",
            "name" : "100_:class com.android.internal.view.IInputConnectionWrapper$MyHandler\"}"
        },
        {
            "value" : "{\"what\":101,\"callbackField\":\"\",\"targetField\":\"class android.app.ActivityThread$H (no class loader)\"}",
            "name" : "101_:class android.app.ActivityThread$H"
        },
        {
            "value" : "{\"what\":104,\"callbackField\":\"\",\"targetField\":\"class android.app.ActivityThread$H (no class loader)\"}",
            "name" : "104_:class android.app.ActivityThread$H"
        },
        {
            "value" : "{\"what\":13,\"callbackField\":\"\",\"targetField\":\"class android.view.ViewRootImpl$ViewRootHandler (no class loader)\"}",
            "name" : "13,_class android.view.ViewRootImpl$ViewRootHandler"
        },
        {
            "value" : "{\"what\":140,\"callbackField\":\"\",\"targetField\":\"class android.app.ActivityThread$H (no class loader)\"}",
            "name" : "140_:class android.app.ActivityThread$H"
        },
        {
            "value" : "{\"what\":149,\"callbackField\":\"\",\"targetField\":\"class android.app.ActivityThread$H (no class loader)\"}",
            "name" : "149_:class android.app.ActivityThread$H"
        },
        {
            "value" : "{\"what\":14,\"callbackField\":\"\",\"targetField\":\"class android.view.ViewRootImpl$ViewRootHandler (no class loader)\"}",
            "name" : "14,_class android.view.ViewRootImpl$ViewRootHandler"
        },
        {
            "value" : "{\"what\":1,\"callbackField\":\"\",\"targetField\":\"class android.os.AsyncTask$InternalHandler (no class loader)\"}",
            "name" : "1_\"targetField\":\"class android.os.AsyncTask$InternalHandler"
        },
        {
            "value" : "{\"what\":1,\"callbackField\":\"\",\"targetField\":\"class android.support.v4.app.FragmentActivity$1 (no class loader)\"}",
            "name" : "1_:class android.support.v4.app.FragmentActivity$1"
        },
        {
            "value" : "{\"what\":22,\"callbackField\":\"\",\"targetField\":\"class android.view.ViewRootImpl$ViewRootHandler (no class loader)\"}",
            "name" : "22,_class android.view.ViewRootImpl$ViewRootHandler"
        },
        {
            "value" : "{\"what\":2,\"callbackField\":\"\",\"targetField\":\"class android.view.inputmethod.InputMethodManager$H (no class loader)\"}",
            "name" : "2_:class android.view.inputmethod.InputMethodManager$H"
        },
        {
            "value" : "{\"what\":3,\"callbackField\":\"\",\"targetField\":\"class android.view.inputmethod.InputMethodManager$H (no class loader)\"}",
            "name" : "3_\"callbackField\":class android.view.inputmethod.InputMethodManager$H"
        },
        {
            "value" : "{\"what\":4,\"callbackField\":\"\",\"targetField\":\"class android.view.inputmethod.InputMethodManager$H (no class loader)\"}",
            "name" : "4_\"callbackField\":class android.view.inputmethod.InputMethodManager$H"
        },
        {
            "value" : "{\"what\":5,\"callbackField\":\"\",\"targetField\":\"class android.view.ViewRootImpl$ViewRootHandler (no class loader)\"}",
            "name" : "5_\"callbackField\":class android.view.ViewRootImpl$ViewRootHandler"
        },
        {
            "value" : "{\"what\":65,\"callbackField\":\"\",\"targetField\":\"class com.android.internal.view.IInputConnectionWrapper$MyHandler (no class loader)\"}",
            "name" : "65_\"callbackField\":class com.android.internal.view.IInputConnectionWrapper$MyHandler"
        },
        {
            "value" : "{\"what\":6,\"callbackField\":\"\",\"targetField\":\"class android.view.ViewRootImpl$ViewRootHandler (no class loader)\"}",
            "name" : "6_\"callbackField\":class android.view.ViewRootImpl$ViewRootHandler"
        },
        {
            "value" : "{\"what\":8,\"callbackField\":\"\",\"targetField\":\"class android.view.ViewRootImpl$ViewRootHandler (no class loader)\"}",
            "name" : "8_\"callbackField\":class android.view.ViewRootImpl$ViewRootHandler"
        },
        {
            "value" : "{\"what\":0,\"callbackField\":\"class android.app.ActivityThread$1 (no class loader)\",\"targetField\":\"class android.view.ViewRootImpl$ViewRootHandler (no class loader)\"}",
            "name" : "0_android.app.ActivityThread$1"
        },
        {
            "value" : "interface android.view.View$OnClickListener (no class loader).onClick(Landroid/view/View;)V",
            "name" : "View.OnClickListener"
        }
    ]
}
