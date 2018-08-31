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
    forwardPostRequest(req, "/completion_search", queryUrl)
  }
  def parseLs = Action { req : Request[AnyContent]  =>
    //    val Token(name, value) = CSRF.getToken.get
    val urltail = "/parse_ls"
    forwardPostRequest(req, urltail, verivitaWebUrl)
  }
  def queryList = Action {req =>
//    Ok(Json.toJson(PreSetQueries.getQueries))
      Ok(Json.toJson(getGithubDoc("list").split("\n")))
  }
  def getDisallowList = Action {req =>
    forwardGetRequest(req, "/get_disallow_list", verivitaWebUrl)
  }

  def verify = Action { req : Request[AnyContent] =>
    req.queryString.get("rule").flatMap(a =>  {
      a.headOption.map { (a: String) =>
        forwardPostRequest(req, s"/verify?rule=${a}", verivitaWebUrl)
      }
    }
    ).getOrElse(BadRequest("Specify rule."))
  }

  def getStatus = Action {req : Request[AnyContent] =>
    req.queryString.get("id").flatMap(a =>  {
      a.headOption.map { (a: String) =>
        forwardGetRequest(req, s"/status?id=${a}", verivitaWebUrl)
      }
    }
    ).getOrElse(BadRequest("Specify rule."))
  }


  private val timeout = Duration(10, "minutes")

  private def forwardPostRequest(req: Request[AnyContent], urltail: String, baseurl : String) = {

    val request: Future[WSResponse] = ws.url(baseurl + urltail)
      .withHttpHeaders("Content-Type" -> "application/json")
      .withRequestTimeout(timeout)
      .post(req.body.asJson.getOrElse(Json.parse("{}")))
    val res = Await.result(request, timeout)
    Ok(res.body)
  }
  private def forwardGetRequest(req: Request[AnyContent], urltail: String, baseurl : String) = {

    val request: Future[WSResponse] = ws.url(baseurl + urltail)
      .withHttpHeaders("Content-Type" -> "application/json")
      .withRequestTimeout(timeout)
      .get()
    val res = Await.result(request, timeout)
    Ok(res.body)
  }
  private def getGithubDoc(name :String) = {
    val request : Future[WSResponse] =
      ws.url(s"https://raw.githubusercontent.com/cuplv/verivita/master/docs/${name}")
        .withRequestTimeout(timeout)
        .get()
    val res = Await.result(request,timeout)
    if (res.status == 200)
      res.body
    else
      ""
  }


  def getQuery(id : String) = Action{ req : Request[AnyContent] =>
//    PreSetQueries.getQuery(id) match{
//      case Some(v) => Ok(v)
//      case None => BadRequest("Query does not exist.")
//    }
    val r  = getGithubDoc(id)
    if (r != "")
      Ok(r)
    else
      BadRequest("Error retrieving query")
  }
  def getQueryDescription(id : String) = Action { req : Request[AnyContent] =>
    val r = getGithubDoc(s"${id}_description")
    if (r != "")
      Ok(r)
    else
      BadRequest("Error retrieving doc.")
  }
}
