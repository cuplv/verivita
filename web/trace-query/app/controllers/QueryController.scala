package controllers

import edu.colorado.plv.QueryTrace.{CCallback, CCallin, CTrace}
import javax.inject._
import play.api.mvc._
import plv.colorado.edu.{CallbackWrapper, CallinWrapper, TraceDbQuery}
import scalapb.json4s.JsonFormat

import scala.util.{Success, Try}

class QueryController @Inject()(cc: ControllerComponents, traceQuery : TraceDbQuery) extends AbstractController(cc){

  def withParsedCTrace[T](json : AnyContent, task : Try[CTrace] => T ) = json match {
    case AnyContentAsJson(a) => task(Try(JsonFormat.fromJsonString[CTrace](a.toString())))
    case _ => ???
  }

  def getSimilarCallbacks() = Action { implicit request : Request[AnyContent] =>

    Ok("To implement")
  }
  def getSimilarCallins() = Action { implicit request: Request[AnyContent] =>

    Ok("To implement")
  }

  def traceSearch(rank : String)  = Action { implicit request : Request[AnyContent] =>

    withParsedCTrace(request.body, { p => p match {
      case Success(p) => {
        if (rank == "any") {
          val traceIDS = traceQuery.traceAnySearch(p)
          val traceIdentifiers = traceIDS.map(traceQuery.dbTrace2TraceIdentifier).map(JsonFormat.toJsonString)
          Ok("[" + traceIdentifiers.mkString(",") + "]")
        }else if(rank == "rank"){
          //TODO: cap number of edges to prevent DDOS

          val traceIDS = traceQuery.traceRankSearch(p)
          val traceIdentifiers = traceIDS.map { a =>
              val identifier = traceQuery.dbTrace2TraceIdentifier(a._1)
              s"""{"rank": ${a._2}, "trace": ${JsonFormat.toJsonString(identifier)}}"""
          }
            //(a._2,JsonFormat.toJsonString(traceQuery.dbTrace2TraceIdentifier(a._1))) )

            //.map(traceQuery.dbTrace2TraceIdentifier).map(JsonFormat.toJsonString)
          Ok("[" + traceIdentifiers.mkString(",") + "]")
        }else {
          badRequest("Valid values: any/rank")
        }
      }
      case _ => ???
      }
    })
  }
  def badRequest(message : String) ={
    BadRequest(s"""{"message":"${message}"}""")
  }

  def completionSearch() = Action{ request : Request[AnyContent] =>
    withParsedCTrace(request.body, {p => p match{
      case Success(p) => {
        val isCallback = traceQuery.isCallbackQuery(p)
        val cicb = isCallback match{
          case Some(true) => "callback"
          case Some(false) => "callin"
          case None => "error"
        }
        //        val traceIDS = traceQuery.traceRankSearch(p)
        val list_res = isCallback match {
          case Some(b) =>
            Some(traceQuery.completionSearch(p,b))
          case None =>
            None
        }
        list_res match{
          case None => badRequest("hole not found")
          case Some(v) =>
            val results = v.map(a => {
              val value: CCallin = a._2 match {
                case CallbackWrapper(c) => ???
                case CallinWrapper(c) => c
              }
              s"""{"rank" : ${a._1}, "${cicb}": ${JsonFormat.toJsonString(value)} }"""
            })
            Ok(s"[${results.mkString(",")}]")
        }
      }
      case _ => badRequest("query parese error")
    }})
  }
  /**
    * Find all methods that contain any of the methods in the query
    */
  def getTracesFromAllMethods() = Action { implicit request: Request[AnyContent] =>

//    request.body match{
//      case AnyContentAsJson(a) => {
//        val protoparse: Try[CTrace] = Try(JsonFormat.fromJsonString[CTrace](a.toString()))
//
//        //TODO: test code to delete
//
//      }
//      case _ => BadRequest("Json Required")
//    }
    withParsedCTrace(request.body, { protoparse =>
        val methods = traceQuery.getMethod(CCallback(methodSignature = "void onCreate(android.os.Bundle)"))
        val params: Seq[traceQuery.DBParam] = traceQuery.getAllParams(methods)
        val traces: Set[Int] =  traceQuery.getTraceId(params)
        Ok("[" + traces.mkString(",") + "]")
      }
    )
  }


  def getMethods() = Action { implicit request : Request[AnyContent] =>
    request.body match{
      case _ => ???
    }
  }

}
