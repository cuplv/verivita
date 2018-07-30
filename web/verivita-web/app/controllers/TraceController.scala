package controllers

import edu.colorado.plv.{TraceManager, TraceMessage, TraceUtils}
import javax.inject._
import play.api._
import play.api.libs.json.{JsArray, JsString}
import play.api.mvc._
import services.Counter

import scala.collection.immutable

/**
  * This controller is responsible for getting traces, searching traces with a query, searching query completions etc
  */
@Singleton
class TraceController @Inject()(counter: Counter, traceManager : TraceManager) extends InjectedController {

  /**
    * Create an action that responds with the [[Counter]]'s current
    * count. The result is plain text. This `Action` is mapped to
    * `GET /count` requests by an entry in the `routes` config file.
    */
  def count = Action {
    val count = counter.nextCount()
    Ok(s"""{ "counter": $count }""")
  }
  def getTraceList = Action{
    val traceList = traceManager.getTraceList()
    Ok(JsArray(traceList.map(JsString)))
  }
  //Params in function are url params
  def trace(traceId: String) = Action {
    val trace = traceManager.getTrace(traceId)
    Ok(JsArray(trace.map(TraceUtils.summarizeMsg)))
  }
  def cxe(traceId: String, disallowId: String) = Action {
    val trace = traceManager.verifyTrace(traceId: String, disallowId: String)
    Ok(JsArray(trace.map(TraceUtils.summarizeMsg)))
  }

}
