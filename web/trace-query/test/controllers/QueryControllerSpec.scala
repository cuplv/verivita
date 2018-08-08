package controllers

import org.scalatestplus.play._
import org.scalatestplus.play.guice._
import play.api.db.Databases
import play.api.test._
import play.api.test.Helpers._
import plv.colorado.edu.{PostgresTraceDbQuery, TraceDbQuery}

class QueryControllerSpec extends PlaySpec with GuiceOneAppPerTest with Injecting {
  val database = Databases(
    driver = "org.postgresql.Driver",
    url = "jdbc:postgresql://localhost:5432/trace_query",
//    name = "mydatabase",
    config = Map(
      "username" -> "postgres",
      "password" -> "72kjnnasi83yhsmmdfh238",
      "jdbcUrl" -> "jdbc:postgresql://localhost:5432/trace_query"
    )
  )
  "QueryController get trace_search/rank" should {
    "connect to test database" in {
      val query = new PostgresTraceDbQuery(database)
      assert(query.testDb(),true)
//      val controller = new QueryController(stubControllerComponents(), query)


    }
  }
}
