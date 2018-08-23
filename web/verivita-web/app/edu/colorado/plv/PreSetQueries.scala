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
        |                            }
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
      """.stripMargin
  )
  def getQueries(): List[String] = queries.keys.toList
  def getQuery(key : String): Option[String] = queries.get(key)
}
