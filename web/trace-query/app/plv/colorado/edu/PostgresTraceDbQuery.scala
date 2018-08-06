package plv.colorado.edu
import java.sql.Connection

import edu.colorado.plv.QueryTrace.{CCallback, CCallin, CTrace, TraceIdentifier}
import javax.inject.Inject
import play.api.db.Database
import anorm._
import anorm.SqlParser.{float, get, scalar, str}

import scala.collection.immutable

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
  private val count_parse = {
    get[Int]("count") map {
      case count => count
    }
  }
  override def getConnectedMethods(method : CCallback): (List[CCallback], List[CCallin]) = {
    ???
  }
  override def getConnectedMethods(method: CCallin): (List[CCallback], List[CCallin]) = ???




  override def getTraceId(params : Seq[DBParam]): Set[Int] = {
    val traceIdParse = {
      get[Int]("trace_id")
    }
    db.withConnection{ conn =>
      implicit val c = conn
      params.flatMap { param =>
        SQL("""SELECT trace_id FROM trace_edge WHERE start_method_param = {param}""")
          .on('param -> param.param_id)
          .as(traceIdParse.*)
      }
    }.toSet
  }

  private val method_id_parse: RowParser[DBMethod] = {
    get[Int]("method_id") ~
      get[String] ("signature") ~
      get[String] ("first_framework_override")map {
      case id ~ sig ~ ov => DBMethod(id,sig,ov)
    }
  }
  override def getMethod(method : CCallback): Seq[DBMethod] = {
    val sig: String = method.methodSignature
    //.on("sig" -> sig)
    db.withConnection { conn =>
      implicit val b = conn
      val sql2: SimpleSql[Row] =
        SQL("""SELECT * FROM method
              WHERE signature = {sig};
           """)

      val sql = sql2.on('sig -> sig)

//      val sql: SimpleSql[Row] =
//        SQL("""SELECT * FROM method
//              WHERE signature = {sig};
//           """).on('sig -> sig)
      val res: immutable.Seq[DBMethod] =
        sql.as(method_id_parse.*)
      res
    }
  }
  val param_parse = {
    get[Int]("param_id")~
    get[Int]("method_id")~
    get[Int]("param_position") map {
      case param_id ~ method_id ~ param_position => DBParam(param_id, param_position, method_id)
    }
  }
  override def getAllParams(methods : Seq[DBMethod]): Seq[DBParam] = {
    db.withConnection{ conn =>
      implicit val connection = conn
      methods.flatMap{ method =>
        SQL("""SELECT * FROM method_param WHERE method_id = {id}""")
          .on('id -> method.method_id).as(param_parse.*)
      }
    }
  }
  override def testDb(): Boolean = {
    db.withConnection{ conn =>
//      val stmt = conn.createStatement
//      val rs = stmt.executeQuery("""select * from pg_catalog.pg_tables;""")
//      val string = rs.toString
      implicit val b: Connection = conn
//      val a = SQL"""select first_name from actor where actor_id > 190;""".as(simple.*)

        val a = SQL"""select count(*) from traces;""".as(count_parse.single)

      a > 0
    }

  }


}
