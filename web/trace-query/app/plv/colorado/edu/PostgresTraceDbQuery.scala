package plv.colorado.edu
import java.sql.Connection

import edu.colorado.plv.QueryTrace._
import javax.inject.Inject
import play.api.db.Database
import anorm._
import anorm.SqlParser.{float, get, scalar, str}
import edu.colorado.plv.QueryTrace
import edu.colorado.plv.QueryTrace.CParam.Param

import scala.collection.immutable

/**
  * note this seems to be the best example of how to draw the rest of the owl:
  * https://github.com/playframework/play-scala-anorm-example/blob/0862ced1fe3e7543f5789540b9edd0cd04271f71/app/models/ComputerRepository.scala#L56:65
  * @param db
  */
class PostgresTraceDbQuery @Inject()(db: Database) extends TraceDbQuery {

  private val method_id_parse: RowParser[DBMethod] = {
    get[Int]("method_id") ~
      get[String] ("signature") ~
      get[String] ("first_framework_override")map {
      case id ~ sig ~ ov => DBMethod(id,sig,ov)
    }
  }
  private val count_parse = {
    get[Int]("count") map {
      case count => count
    }
  }
  val param_parse = {
    get[Int]("param_id")~
      get[Int]("method_id")~
      get[Int]("param_position") map {
      case param_id ~ method_id ~ param_position => DBParam(param_id, param_position, method_id)
    }
  }
  val dbtrace_parse = {
    get[Int]("trace_id") map {
      case trace_id => DBTrace(trace_id)
    }
  }
  //app name, git_repo, trace_name
  val trace_identifier_parser = {
    get[String]("app_name") ~
    get[String]("git_repo") ~
    get[String]("trace_name") map {
      case app_name ~ git_repo ~ trace_name =>
        TraceIdentifier(appName = app_name, gitRepo = git_repo, traceName = trace_name)
    }

  }

  def getDBParam(position : Int, method_id : Int): DBParam = {
    db.withConnection{ conn =>
      implicit val a = conn
      SQL(
        """SELECT * FROM method_param
           WHERE method_id = {method_id}
              AND param_position = {position};
        """).on('method_id -> method_id).on('position -> position).as(param_parse.single)
    }
  }
  def varsFromCCallback(cmd : CallbackOrHole) : Seq[(String,DBParam)] = {
    if(cmd.command.isCallback) varsFromCCallback(cmd.getCallback) else Seq()
  }
  def varsFromCCallback(callback : CCallback): Seq[(String, DBParam)] ={
    //Note can be multiple methods if not fully specified
    val methods = getMethod(callback)

    def protoParams2DBParam(a : Seq[Option[CParam]]) = a flatMap {b => b match{
      case Some(CParam(Param.Variable(CVariable(name)))) =>
        val a: Seq[(String,DBParam)] = methods.map( a => (name,getDBParam(1,a.method_id)))
        a
      case _ => Seq[(String,DBParam)]()
    }}

    val retList: Seq[(String,DBParam)] = protoParams2DBParam(Seq(callback.returnValue))
    val recList: Seq[(String, DBParam)] = protoParams2DBParam(Seq(callback.receiver))
    val paramList: Seq[(String, DBParam)] = protoParams2DBParam(callback.parameters.map(a => Some(a)))

    val out: Seq[(String,DBParam)] =
      callback.nestedCommands.flatMap(varsFromCCallin) ++ retList ++ recList ++ paramList
    out
  }
  def varsFromCCallin( cmd : CCommand): Seq[(String,DBParam)] = {
    if(cmd.command.isCallin) {
      val callin = cmd.getCallin
      val methods = getMethod(callin)
      def protoParams2DBParam(a: Seq[CParam]) = a flatMap { b =>
        b match {
          case CParam(Param.Variable(CVariable(name))) =>
            val a: Seq[(String, DBParam)] = methods.map(a => (name, getDBParam(1, a.method_id)))
            a
          case _ => Seq[(String, DBParam)]()
        }
      }
      val retList = protoParams2DBParam(Seq(callin.getReturnValue))
      val recList = protoParams2DBParam(Seq(callin.getReceiver))
      val paramList = protoParams2DBParam(callin.parameters)

      callin.nestedCallbacks.flatMap(varsFromCCallback) ++ retList ++ recList ++ paramList
    }else{Seq()}

  }
  /**
    * search for similar traces to parameterized query
    *
    * @param trace_query parameterized trace to search for similar
    * @return list of traces sharing any connection with query
    */
  override def traceAnySearch(trace_query: CTrace): Seq[DBTrace] = {
    trace_query.callbacks.flatMap { a =>
      val vars : Seq[(String, DBParam)] = (a.command.callback map varsFromCCallback).getOrElse(???)
      //Generate all pairs where variables are the same and dbparam is different
      //TODO: Note that if something is used twice in one method it will show up as an edge is this a problem?
      val edges = for (x <- vars ; y <- vars
                       if (x._1 == y._1) && //variable matches
                         (x._2 != y._2) && //no parameter self loops
                         (x._2.param_id < y._2.param_id)) //don't generate duplicate reverse order pairs
        yield (x._2.param_id, y._2.param_id)

      db.withConnection{ implicit conn =>
        edges flatMap { edge =>
          SQL(
            """SELECT DISTINCT trace_id FROM trace_edge
            WHERE start_method_param = {sp} AND end_method_param = {ep};""")
            .on('sp -> edge._1).on('ep -> edge._2).as(dbtrace_parse.*)
        }
      }
    }
  }

  override def traceRankSearch(trace_query: CTrace): Seq[(DBTrace,Int)] = {
    //TODO: This currently makes a db query for every edge in user query, may be more efficient way
    //Currently calculate power set of edges and calculate traces for each
    val edgeTraceMap: Map[(Int, Int), Set[DBTrace]] = traceSearch(trace_query)
    //Loop through edge trace map and count the number of times a given trace appears
    val ranked = edgeTraceMap.foldLeft(Map[DBTrace, Int]()) { (acc: Map[DBTrace, Int], v: ((Int, Int), Set[DBTrace])) =>
      v._2.foldLeft(acc) { (acc2: Map[DBTrace, Int], v2: DBTrace) => acc2 + (v2 -> (acc.getOrElse(v2, 0) + 1)) }
    }.toList
    ranked.sortWith( _._2 < _._2)
  }
  override def traceSearch(trace_query: CTrace): Map[(Int, Int), Set[DBTrace]] = {
    trace_query.callbacks.map { a =>
      val varAttempt = a.command.callback map varsFromCCallback
      val vars : Seq[(String, DBParam)] = varAttempt match{
        case Some(v) => v
        case None => {
          Seq()
        }
      }
//        varAttempt.getOrElse(
//          ???
//        )
      //Generate all pairs where variables are the same and dbparam is different
      //TODO: Note that if something is used twice in one method it will show up as an edge is this a problem?
      val edges = for (x <- vars ; y <- vars
                       if (x._1 == y._1) && //variable matches
                         (x._2 != y._2) && //no parameter self loops
                         (x._2.param_id < y._2.param_id)) //don't generate duplicate reverse order pairs
        yield (x._2.param_id, y._2.param_id)

      db.withConnection { implicit conn =>
        edges.foldLeft(Map[(Int, Int), Set[DBTrace]]()) { (acc, edge) =>
          val newEdges = SQL(
            """SELECT DISTINCT trace_id FROM trace_edge
            WHERE start_method_param = {sp} AND end_method_param = {ep};""")
            .on('sp -> edge._1).on('ep -> edge._2).as(dbtrace_parse.*).toSet
          val oldSet = acc.getOrElse(edge, Set())
          val r: Map[(Int, Int), Set[DBTrace]] = acc + (edge -> (newEdges.union(oldSet)))
          r
        }
      }
    }.foldLeft(Map[(Int, Int), Set[DBTrace]]()) { (acc,v) => acc ++ v}
  }

  override def dbTrace2TraceIdentifier(dbtrace: DBTrace): TraceIdentifier = {
    db.withConnection{implicit conn =>
      SQL("""SELECT * FROM traces WHERE trace_id = {id};""")
        .on('id -> dbtrace.trace_id).as(trace_identifier_parser.single)
    }
  }

  /**
    * search for completions to missing callbacks
    *
    * @param completion_query
    * @return
    */
  override def callinCompletionSearch(completion_query: CTrace): List[(Int,CCallin)] = {
    val traceIDs = traceRankSearch(completion_query)
    val methodsInQuery: Seq[(String, DBParam)] =
      completion_query.callbacks.flatMap(varsFromCCallback)
    val everypair = for( traceId <- traceIDs; method <- methodsInQuery)
      yield (traceId,method)
    //TODO: query for method and one of the methods,
    // join together the method/var,
    // rank based on connections as well as trace score (multiply?)
    ???
  }

  /**
    * search for completions to missing callins
    *
    * @param completion_query query where a callin
    * @return
    */
override def callbackCompletionSearch(completion_query: CTrace): List[(Int,CCallback)] = {
  ???
}

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


  def getMethod(method : CCallin): Seq[DBMethod] = {
    val sig = method.methodSignature
    val fmwk = method.frameworkClass
    getMethod(sig,fmwk,false)
  }
  override def getMethod(method : CCallback): Seq[DBMethod] = {
    val sig: String = method.methodSignature
    val fmwk : String = method.firstFrameworkOverrrideClass
    //.on("sig" -> sig)
    getMethod(sig, fmwk,true)
  }

  private def getMethod(sig: String, fmwk: String, isCallback : Boolean) = {
    db.withConnection { conn =>
      implicit val b = conn

      val sql2: SimpleSql[Row] = if (sig != "" && fmwk == "") {

        SQL(
          """SELECT * FROM method
              WHERE signature = {sig} AND is_callback = {cb};
           """)
      } else if (sig != "" && fmwk != "") {
        SQL(
          """SELECT * FROM method
              WHERE signature = {sig} AND first_framework_override = {fmwk} AND is_callback = {cb};
           """)
      } else if (sig == "" && fmwk != "") {
        SQL(
          """SELECT * FROM method
              WHERE signature = {sig} AND first_framework_override = {fmwk} AND is_callback = {cb};
           """)
      }
      else {
        ???
      }

      val sql = sql2.on('sig -> sig).on('fmwk -> fmwk).on('cb -> isCallback)

      //      val sql: SimpleSql[Row] =
      //        SQL("""SELECT * FROM method
      //              WHERE signature = {sig};
      //           """).on('sig -> sig)
      val res: immutable.Seq[DBMethod] =
      sql.as(method_id_parse.*)
      res
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


  def findEnabledHole_(c :CallbackOrHole) : Option[Boolean] = {
    if(c.command.isHole){
      Some(true)
    }else{
      val maybeBooleans: Seq[Option[Boolean]] =
        c.getCallback.nestedCommands.map(findEnabledHole).filter(a => !a.isEmpty)
      maybeBooleans match {
        case Seq() => None
        case a => a.head
      }
    }
  }
  def findEnabledHole(c : CCommand) : Option[Boolean] = {
    if(c.command.isHole){
      Some(false)
    }else{
      //TODO: nested callbacks ignored, is this reasonable?
      None
    }
  }

  /**
    *
    * @param c
    * @return Some(true) if hole is callback Some(false) if callin None if malformed
    */
  override def isCallbackQuery(c: CTrace): Option[Boolean] = {
    c.callbacks.map(findEnabledHole_).filter(a => !a.isEmpty) match{
      case Seq() => None
      case a => a.head

    }
  }
}
