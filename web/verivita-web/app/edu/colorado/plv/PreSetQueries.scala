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
    "execute_alarm" ->
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
      |                            "frameworkClass": "android.view.View android.app.Activity.findViewById(int)",
      |                            "methodSignature": "android.view.View findViewById(int)",
      |                            "parameters": [
      |                                {
      |                                    "variable": {
      |                                        "name": "z"
      |                                    }
      |                                }
      |                            ],
      |                            "receiver": {
      |                                "variable": {
      |                                    "name": "a"
      |                                }
      |                            },
      |                            "returnValue": {
      |                                "variable": {
      |                                    "name": "b"
      |                                }
      |                            }
      |                        }
      |                    },
      |                    {
      |                        "callin": {
      |                            "frameworkClass": "void android.view.View.setOnClickListener(android.view.View$OnClickListener)",
      |                            "methodSignature": "void setOnClickListener(android.view.View$OnClickListener)",
      |                            "parameters": [
      |                                {
      |                                    "variable": {
      |                                        "name": "l"
      |                                    }
      |                                }
      |                            ],
      |                            "receiver": {
      |                                "variable": {
      |                                    "name": "b"
      |                                }
      |                            },
      |                            "returnValue": {
      |                                "prHole": {}
      |                            }
      |                        }
      |                    },
      |                    {
      |                        "callin": {
      |                            "frameworkClass": "void android.os.AsyncTask.<init>()",
      |                            "methodSignature": "void <init>()",
      |                            "receiver": {
      |                                "variable": {
      |                                    "name": "t"
      |                                }
      |                            },
      |                            "returnValue": {
      |                                "prHole": {}
      |                            }
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
      |        },
      |        {
      |            "callback": {
      |                "firstFrameworkOverrrideClass": "void android.app.Activity.onResume()",
      |                "methodSignature": "void onResume()",
      |                "receiver": {
      |                    "variable": {
      |                        "name": "a"
      |                    }
      |                }
      |            }
      |        },
      |        {
      |            "callback": {
      |                "firstFrameworkOverrrideClass": "void android.view.View$OnClickListener.onClick(android.view.View)",
      |                "methodSignature": "void onClick(android.view.View)",
      |                "nestedCommands": [
      |                    {
      |                        "callin": {
      |                            "frameworkClass": "android.os.AsyncTask android.os.AsyncTask.execute(java.lang.Object[])",
      |                            "methodSignature": "android.os.AsyncTask execute(java.lang.Object[])",
      |                            "parameters": [
      |                                {
      |                                    "prHole": {}
      |                                }
      |                            ],
      |                            "receiver": {
      |                                "variable": {
      |                                    "name": "t"
      |                                }
      |                            },
      |                            "returnValue": {
      |                                "prHole": {}
      |                            }
      |                        }
      |                    }
      |                ],
      |                "parameters": [
      |                    {
      |                        "variable": {
      |                            "name": "b"
      |                        }
      |                    }
      |                ],
      |                "receiver": {
      |                    "variable": {
      |                        "name": "l"
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
