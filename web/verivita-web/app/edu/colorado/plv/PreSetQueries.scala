package edu.colorado.plv

object PreSetQueries {
  val queries = Map(
    "create_systemsvc" ->
      """
        |{
        |    "callbacks": [
        |        {
        |            "callback": {
        |                "firstFrameworkOverrrideClass": "void android.app.Activity.onCreate(android.os.Bundle)",
        |                "methodSignature": "void onCreate(android.os.Bundle)",
        |                "nestedCommands": [
        |                    {
        |                        "callin": {
        |                            "frameworkClass": "java.lang.Object android.app.Activity.getSystemService(java.lang.String)",
        |                            "methodSignature": "java.lang.Object getSystemService(java.lang.String)",
        |                            "receiver": {
        |                                "variable": {
        |                                    "name": "a"
        |                                }
        |                            },
        |                            "returnValue": {
        |                                "prHole": {}
        |                            },
        |                            "parameters": [
        |                               {
        |                                 "prHole":{}
        |                               }
        |                            ]
        |                        }
        |                    },
        |                    {
        |                        "ciHole": {
        |                            "isSelected": true
        |                        }
        |                    }
        |                ],
        |                "parameters": [
        |                    {
        |                        "prHole": {}
        |                    }
        |                ],
        |                "receiver": {
        |                    "variable": {
        |                        "name": "a"
        |                    }
        |                }
        |            }
        |        }
        |    ]
        |}
        |
      """.stripMargin,
    "execute_alarm" -> """{"callbacks":[{"callback":{"methodSignature":"void <init>()","firstFrameworkOverrrideClass":"void android.app.Activity.<init>()","receiver":{"variable":{"name":"a"}}}},{"callback":{"methodSignature":"void onCreate(android.os.Bundle)","firstFrameworkOverrrideClass":"void android.app.Activity.onCreate(android.os.Bundle)","parameters":[{"prHole":{}}],"receiver":{"variable":{"name":"a"}},"nestedCommands":[{"callin":{"methodSignature":"android.view.View findViewById(int)","frameworkClass":"android.view.View android.app.Activity.findViewById(int)","parameters":[{"variable":{"name":"z"}}],"receiver":{"variable":{"name":"a"}},"returnValue":{"variable":{"name":"b"}}}},{"callin":{"methodSignature":"void setOnClickListener(android.view.View$OnClickListener)","frameworkClass":"void android.view.View.setOnClickListener(android.view.View$OnClickListener)","parameters":[{"variable":{"name":"l"}}],"receiver":{"variable":{"name":"b"}},"returnValue":{"prHole":{}}}},{"callin":{"methodSignature":"void <init>()","frameworkClass":"void android.os.AsyncTask.<init>()","receiver":{"variable":{"name":"t"}},"returnValue":{"prHole":{}}}}]}},{"callback":{"methodSignature":"void onStart()","firstFrameworkOverrrideClass":"void android.app.Activity.onStart()","receiver":{"variable":{"name":"a"}}}},{"callback":{"methodSignature":"void onResume()","firstFrameworkOverrrideClass":"void android.app.Activity.onResume()","receiver":{"variable":{"name":"a"}}}},{"callback":{"methodSignature":"void onClick(android.view.View)","firstFrameworkOverrrideClass":"void android.view.View$OnClickListener.onClick(android.view.View)","parameters":[{"variable":{"name":"b"}}],"receiver":{"variable":{"name":"l"}},"nestedCommands":[{"callin":{"methodSignature":"android.os.AsyncTask execute(java.lang.Object[])","frameworkClass":"android.os.AsyncTask android.os.AsyncTask.execute(java.lang.Object[])","parameters":[{"prHole":{}}],"receiver":{"variable":{"name":"t"}},"returnValue":{"prHole":{}}}}]}}]}""",
    "execute_safe" -> """{"callbacks":[{"callback":{"methodSignature":"void <init>()","firstFrameworkOverrrideClass":"void android.app.Activity.<init>()","receiver":{"variable":{"name":"a"}}}},{"callback":{"methodSignature":"void onCreate(android.os.Bundle)","firstFrameworkOverrrideClass":"void android.app.Activity.onCreate(android.os.Bundle)","parameters":[{"prHole":{}}],"receiver":{"variable":{"name":"a"}},"nestedCommands":[{"callin":{"methodSignature":"android.view.View findViewById(int)","frameworkClass":"android.view.View android.app.Activity.findViewById(int)","parameters":[{"variable":{"name":"z"}}],"receiver":{"variable":{"name":"a"}},"returnValue":{"variable":{"name":"b"}}}},{"callin":{"methodSignature":"void setOnClickListener(android.view.View$OnClickListener)","frameworkClass":"void android.view.View.setOnClickListener(android.view.View$OnClickListener)","parameters":[{"variable":{"name":"l"}}],"receiver":{"variable":{"name":"b"}},"returnValue":{"prHole":{}}}},{"callin":{"methodSignature":"void <init>()","frameworkClass":"void android.os.AsyncTask.<init>()","receiver":{"variable":{"name":"t"}},"returnValue":{"prHole":{}}}}]}},{"callback":{"methodSignature":"void onStart()","firstFrameworkOverrrideClass":"void android.app.Activity.onStart()","receiver":{"variable":{"name":"a"}}}},{"callback":{"methodSignature":"void onResume()","firstFrameworkOverrrideClass":"void android.app.Activity.onResume()","receiver":{"variable":{"name":"a"}}}},{"callback":{"methodSignature":"void onClick(android.view.View)","firstFrameworkOverrrideClass":"void android.view.View$OnClickListener.onClick(android.view.View)","parameters":[{"variable":{"name":"b"}}],"receiver":{"variable":{"name":"l"}},"nestedCommands":[{"callin":{"methodSignature":"void setEnabled(boolean)","frameworkClass":"void android.widget.TextView.setEnabled(boolean)","parameters":[{"primitive":{"boolVal":false}}],"receiver":{"variable":{"name":"b"}},"returnValue":{"prHole":{}}}},{"callin":{"methodSignature":"android.os.AsyncTask execute(java.lang.Object[])","frameworkClass":"android.os.AsyncTask android.os.AsyncTask.execute(java.lang.Object[])","parameters":[{"prHole":{}}],"receiver":{"variable":{"name":"t"}},"returnValue":{"prHole":{}}}}]}}]}""",
//    "execute_error_2" -> """{"callbacks":[{"callback":{"methodSignature":"void onCreate(android.os.Bundle)","firstFrameworkOverrrideClass":"void android.app.Activity.onCreate(android.os.Bundle)","parameters":[{"prHole":{}}],"receiver":{"variable":{"name":"a"}},"nestedCommands":[{"callin":{"methodSignature":"android.view.View findViewById(int)","frameworkClass":"android.view.View android.app.Activity.findViewById(int)","parameters":[{"variable":{"name":"z"}}],"receiver":{"variable":{"name":"a"}},"returnValue":{"variable":{"name":"b"}}}},{"callin":{"methodSignature":"void setOnClickListener(android.view.View$OnClickListener)","frameworkClass":"void android.view.View.setOnClickListener(android.view.View$OnClickListener)","parameters":[{"variable":{"name":"l"}}],"receiver":{"variable":{"name":"b"}},"returnValue":{"prHole":{}}}},{"callin":{"methodSignature":"void <init>()","frameworkClass":"void android.os.AsyncTask.<init>()","receiver":{"variable":{"name":"t"}},"returnValue":{"prHole":{}}}}]}},{"callback":{"methodSignature":"void onResume()","firstFrameworkOverrrideClass":"void android.app.Activity.onResume()","receiver":{"variable":{"name":"a"}}}},{"callback":{"methodSignature":"void onClick(android.view.View)","firstFrameworkOverrrideClass":"void android.view.View$OnClickListener.onClick(android.view.View)","parameters":[{"variable":{"name":"b"}}],"receiver":{"variable":{"name":"l"}},"nestedCommands":[{"callin":{"methodSignature":"android.os.AsyncTask execute(java.lang.Object[])","frameworkClass":"android.os.AsyncTask android.os.AsyncTask.execute(java.lang.Object[])","parameters":[{"prHole":{}}],"receiver":{"variable":{"name":"t"}},"returnValue":{"prHole":{}}}}]}}]}""",
    "trivial_execute_fail" -> """{"callbacks":[{"callback":{"methodSignature":"void <init>()","firstFrameworkOverrrideClass":"void android.app.Activity.<init>()","receiver":{"variable":{"name":"a"}}}},{"callback":{"methodSignature":"void onCreate(android.os.Bundle)","firstFrameworkOverrrideClass":"void android.app.Activity.onCreate(android.os.Bundle)","parameters":[{"prHole":{}}],"receiver":{"variable":{"name":"a"}},"nestedCommands":[{"callin":{"methodSignature":"android.os.AsyncTask execute(java.lang.Object[])","frameworkClass":"android.os.AsyncTask android.os.AsyncTask.execute(java.lang.Object[])","parameters":[{"prHole":{}}],"receiver":{"variable":{"name":"t"}},"returnValue":{"variable":{"name":"t"}}}},{"callin":{"methodSignature":"android.os.AsyncTask execute(java.lang.Object[])","frameworkClass":"android.os.AsyncTask android.os.AsyncTask.execute(java.lang.Object[])","parameters":[{"prHole":{}}],"receiver":{"variable":{"name":"t"}},"returnValue":{"variable":{"name":"t"}}}}]}}]}"""

  )
  def getQueries(): List[String] = queries.keys.toList
  def getQuery(key : String): Option[String] = queries.get(key)
}
