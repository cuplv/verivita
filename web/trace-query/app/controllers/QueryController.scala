package controllers

import edu.colorado.plv.QueryTrace.{CCallback, CTrace}
import javax.inject._
import play.api.mvc._
import plv.colorado.edu.TraceDbQuery
import scalapb.json4s.JsonFormat

import scala.util.Try

class QueryController @Inject()(cc: ControllerComponents, traceQuery : TraceDbQuery) extends AbstractController(cc){

  def withParsedProto[T](json : AnyContent, task : Try[CTrace] => T ) = json match {
    case AnyContentAsJson(a) => task(Try(JsonFormat.fromJsonString[CTrace](a.toString())))
    case _ => ???
  }

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
    withParsedProto(request.body, { protoparse =>
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
