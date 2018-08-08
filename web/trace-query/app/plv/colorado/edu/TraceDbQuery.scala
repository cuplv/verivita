package plv.colorado.edu

import edu.colorado.plv.QueryTrace.{CCallback, CCallin, CTrace, TraceIdentifier}

trait TraceDbQuery {

  def testDb() : Boolean
  /**
    * search for similar traces to parameterized query
    * @param trace_query parameterized trace to search for similar
    * @return list of traces sharing any connection with query
    */
  def traceAnySearch(trace_query : CTrace) : Seq[DBTrace]

  /**
    * search for traces including most edges
    * @param trace_query
    * @return results ranked by number of edges included by trace
    */
  def traceRankSearch(trace_query : CTrace) : Seq[(DBTrace, Int)]

  /**
    * Search for traces with a given connection
    * @param trace_query
    * @return edges from query, represented by int pair mapped to traces
    */
  def traceSearch(trace_query : CTrace) : Map[(Int,Int), Set[DBTrace]]


  def dbTrace2TraceIdentifier(dbtrace : DBTrace) : TraceIdentifier

  def isCallbackQuery(c : CTrace): Option[Boolean]

  /**
    * search for completions to missing callbacks
    * @param completion_query
    * @return
    */
  def callinCompletionSearch( completion_query : CTrace) : List[CCallin]

  /**
    * search for completions to missing callins
    * @param completion_query query where a callin
    * @return
    */
  def callbackCompletionSearch( completion_query : CTrace) : List[CCallback]

  /**
    * get trace data based on identifier, note the traceIdentifier is a unique key
    * @param identifier identifier used to find trace
    * @return ctrace matching identifier
    */
  def getTrace(identifier: TraceIdentifier) : CTrace

  def getTraceId(params : Seq[DBParam]) : Set[Int]

  def getConnectedMethods(method : CCallback): (List[CCallback], List[CCallin])
  def getConnectedMethods(method : CCallin) : (List[CCallback], List[CCallin])
  def getMethod(method : CCallback): Seq[DBMethod]
  def getAllParams(methods: Seq[DBMethod]): Seq[DBParam]
  case class DBEdge(edge_id : Int, start_method_param : Int, end_method_param : Int)
  case class DBMethod(method_id : Int, signature: String, firstFramework: String)
  case class DBParam(param_id: Int, param_position : Int, method_id : Int)
  case class DBTrace(trace_id : Int)
}
