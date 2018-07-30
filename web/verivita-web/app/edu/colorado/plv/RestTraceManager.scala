package edu.colorado.plv

class RestTraceManager extends TraceManager {
  override def verifyTrace(traceId: String, disallowId: String): List[TraceMessage] = ???

  override def getTrace(id: String): List[TraceMessage] = ???

  override def getTraceList(): List[String] = ???
}
