package plv.colorado.edu
import edu.colorado.plv.QueryTrace.{CCallback, CCallin, CTrace, TraceIdentifier}
import javax.inject.Inject
import play.api.db.Database

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

  override def testDb(): Boolean = {
    db.withConnection{ conn =>
      val stmt = conn.createStatement
      val rs = stmt.executeQuery("""select * from pg_catalog.pg_tables;""")
      val string = rs.toString
      ???
    }
//    ???
  }
}
