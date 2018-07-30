package controllers

import edu.colorado.plv.QueryTrace.CTrace
import javax.inject._
import play.api.mvc._
import scalapb.json4s.JsonFormat

import scala.util.Try

class QueryController @Inject()(cc: ControllerComponents) extends AbstractController(cc){

  def getTraces() = Action { implicit request: Request[AnyContent] =>

    request.body match{
      case AnyContentAsJson(a) => {
        val protoparse = Try(JsonFormat.fromJsonString[CTrace](a.toString()))
        Ok(a.toString())
      }
      case _ => BadRequest("Json Required")
    }
  }

}
