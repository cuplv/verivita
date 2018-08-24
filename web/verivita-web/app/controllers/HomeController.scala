package controllers

import edu.colorado.plv.PreSetQueries
import javax.inject._
import play.api.libs.ws.{WSBody, WSClient, WSRequest, WSResponse}
import play.api.mvc._

import scala.concurrent.duration.Duration
import play.api.libs.json.Json

import scala.concurrent.{Await, ExecutionContext, Future}


/**
 * This controller creates an `Action` to handle HTTP requests to the
 * application's home page.
 */
@Singleton
class HomeController @Inject() (ws : WSClient) (implicit ec : ExecutionContext) extends InjectedController {

  /**
   * Create an Action to render an HTML page with a welcome message.
   * The configuration in the `routes` file means that this method
   * will be called when the application receives a `GET` request with
   * a path of `/`.
   */
  def index = Action {
    Ok(views.html.main())
  }

  val verivitaWebUrl = sys.env("VERIVITA_WEB_URL")
  val queryUrl = sys.env("TRACEQUERY_WEB_URL")

  def completionSearch = Action { req : Request[AnyContent] =>
    forwardRequest(req, "/completion_search", queryUrl)
  }
  def parseLs = Action { req : Request[AnyContent]  =>
    //    val Token(name, value) = CSRF.getToken.get
    val urltail = "/parse_ls"
    forwardRequest(req, urltail, verivitaWebUrl)
  }
  def queryList = Action {req =>
    Ok(Json.toJson(PreSetQueries.getQueries))
  }

  def verify = Action { req : Request[AnyContent] =>
    forwardRequest(req, "/verify", verivitaWebUrl)
  }


  private def forwardRequest(req: Request[AnyContent], urltail: String, baseurl : String) = {

    val request: Future[WSResponse] = ws.url(baseurl + urltail)
      .withHttpHeaders("Content-Type" -> "application/json")
      .post(req.body.asJson.getOrElse(???))
    val res = Await.result(request, Duration(1, "minutes"))
    Ok(res.body)
  }
  def getQuery(id : String) = Action{ req : Request[AnyContent] =>
    PreSetQueries.getQuery(id) match{
      case Some(v) => Ok(v)
      case None => BadRequest("Query does not exist.")
    }
  }
}
