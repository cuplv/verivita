package edu.colorado.plv

import com.google.inject.Singleton

@Singleton
class FakeManager extends TraceManager {
  def getTrace(id: String): List[TraceMessage]= List(
    TraceMessage(MsgBack, Callback, Some(MethodIdentifier("onCreate", "MyActivity", "com.example"))),
    TraceMessage(MsgIn, Callback, Some(MethodIdentifier("onCreate", "MyActivity", "com.example")))
  )
  def verifyTrace(traceId: String, disallowId: String): List[TraceMessage] = List(
    TraceMessage(MsgBack, Callback, Some(MethodIdentifier("onCreate", "MyActivity", "com.example"))),
    TraceMessage(MsgIn, Callback, Some(MethodIdentifier("onCreate", "MyActivity", "com.example")))
  )
  def getTraceList(): List[String] = List("1","2","3","4")
}
