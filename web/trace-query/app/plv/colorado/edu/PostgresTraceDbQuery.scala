package plv.colorado.edu
import java.sql.Connection

import edu.colorado.plv.QueryTrace.{CCallback, CCallin, CTrace, TraceIdentifier}
import javax.inject.Inject
import play.api.db.Database

import anorm._
import anorm.SqlParser.{ str, float , get , scalar }

/**
  * note this seems to be the best example of how to draw the rest of the owl:
  * https://github.com/playframework/play-scala-anorm-example/blob/0862ced1fe3e7543f5789540b9edd0cd04271f71/app/models/ComputerRepository.scala#L56:65
  * @param db
  */
class PostgresTraceDbQuery @Inject()(db: Database) extends TraceDbQuery {

  /**
    * search for similar traces to parameterized query
    *
    * @param trace_query parameterized trace to search for similar
    * @return list of CTrace without callbacks populated, used to identify traces
    */
  override def traceSearch(trace_query: CTrace): List[TraceIdentifier] = ???

  /**
    * search for completions to missing callbacks
    *
    * @param completion_query
    * @return
    */
  override def callinCompletionSearch(completion_query: CTrace): List[CCallin] = ???

  /**
    * search for completions to missing callins
    *
    * @param completion_query query where a callin
    * @return
    */
override def callbackCompletionSearch(completion_query: CTrace): List[CCallback] = ???

  /**
    * get trace data based on identifier, note the traceIdentifier is a unique key
    *
    * @param identifier identifier used to find trace
    * @return ctrace matching identifier
    */
  override def getTrace(identifier: TraceIdentifier): CTrace = ???

  private val simple = {
    get[String]("first_name")  map {
      case  first_name => first_name
    }
  }
  override def testDb(): Boolean = {
    db.withConnection{ conn =>
//      val stmt = conn.createStatement
//      val rs = stmt.executeQuery("""select * from pg_catalog.pg_tables;""")
//      val string = rs.toString
      implicit val b: Connection = conn
      val a = SQL"""select first_name from actor where actor_id > 190;""".as(simple.*)
//      val query = SQL("""select first_name from actor where actor_id > 190;""")
//      val result = query(conn)
//      val result2 = query.executeQuery()(conn).as(SqlParser.str("first_name").collect)(conn)
//      result2 match{
//        case SqlQueryResult(a,b) => {
//          println(a)
//          println(b)
//          ???
//        }
//      }

      ???
    }

  }
}
