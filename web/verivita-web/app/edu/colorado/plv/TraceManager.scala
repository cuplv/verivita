package edu.colorado.plv

import play.api.libs.json.{JsObject, JsString}

trait TraceManager {
  def getTrace(id: String): List[TraceMessage]
  def getTraceList(): List[String]
}

object TraceUtils {
  def internalException() = "__Internal Problem Encountered__"
  def summarizeMsg(traceMessage: TraceMessage): JsObject ={
    val stackDescriptor: String = traceMessage match{
      case TraceMessage(_, Callback,_) => "Callback"
      case TraceMessage(_, Callin,_) => "Callin"
    }
    val opDescriptor: String = traceMessage match{
      case TraceMessage(MsgException, _, _) => "Exception"
      case TraceMessage(_, _, Some(MethodIdentifier(name, clazz, pkg))) => s"${pkg}.${clazz}.${name}"
      case _ => internalException()
    }
    val directionIdent: String = traceMessage match{
      case TraceMessage(MsgIn , Callback, _) => "Exit"
      case TraceMessage(MsgBack, Callback, _) => "Entry"
      case TraceMessage(MsgIn, Callin, _) => "Entry"
      case TraceMessage(MsgBack, Callin, _) => "Exit"
      case TraceMessage(MsgException, Callback, _) => "Exit"
      case TraceMessage(MsgException, Callin, _) => "Exit"
    }
    JsObject(List(
      ("stackDescriptor", JsString(stackDescriptor)),
      ("opDescriptor", JsString(opDescriptor)),
      ("directionIdent", JsString(directionIdent))
    ))
  }
}

case class TraceMessage(direction: MsgDirection,
                        cicb: MsgCICB,
                        method: Option[MethodIdentifier])

sealed trait MsgDirection

case object MsgIn extends MsgDirection
case object MsgBack extends MsgDirection
case object MsgException extends MsgDirection
//callback exception is app throwing exception
//callin exception is framework throwing exception

sealed trait MsgCICB

case object Callback extends MsgCICB
case object Callin extends MsgCICB

case class MethodIdentifier(name: String, clazz: String, pkg: String)