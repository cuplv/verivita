package edu.colorado.plv

class VerivitaManager extends TraceManager {
  def getTrace(id: String): List[TraceMessage]= List(
    TraceMessage(MsgBack, Callback, Some(MethodIdentifier("onCreate", "MyActivity", "com.example"))),
    TraceMessage(MsgIn, Callback, Some(MethodIdentifier("onCreate", "MyActivity", "com.example")))
  )
  def getTraceList(): List[String] = List("1","2","3","4")
}


