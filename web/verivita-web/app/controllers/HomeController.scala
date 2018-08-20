package controllers

import javax.inject._
import play.api.libs.ws.{WSBody, WSClient, WSRequest, WSResponse}
import play.api.mvc._
import scala.concurrent.duration.Duration

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

  def completionSearch = Action { request : Request[AnyContent] =>
    ???
  }


  //TODO: this is a get because of CSRF filter issues, should fix later
  def parseLs = Action { req : Request[AnyContent]  =>
//    val Token(name, value) = CSRF.getToken.get
    val verivitaWebUrl = sys.env("VERIVITA_WEB_URL")
    val request: Future[WSResponse] = ws.url(verivitaWebUrl + "/parse_ls")
      .withHttpHeaders("Content-Type" -> "application/json")
      .post(req.body.asJson.getOrElse(???))
//    val crequest : WSRequest = request.addHttpHeaders("Accept" -> "application/json")
//      .withMethod("POST")
//      .withBody(req.body.asJson)

    val res = Await.result(request, Duration(1, "minutes"))
    Ok(res.body)
  }

}
