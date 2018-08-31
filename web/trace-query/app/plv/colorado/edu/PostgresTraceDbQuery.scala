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
      get[String] ("first_framework_override") ~
      get[Boolean] ("is_callback") map {
      case id ~ sig ~ ov ~ is_callback => DBMethod(id,sig,ov, is_callback)
    }
  }
  private val count_parse = {
    get[Int]("count") map {
      case count => count
    }
  }
  private val param_parse=  {
    get[Int]("param_id") ~
      get[Int]("method_id") ~
      get[Int]("param_position") map {
      case param_id ~ method_id ~ param_position =>
        ((d : DBMethod) => DBParam(param_id, param_position, method_id,d))
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

  def getDBParam(position : Int, method: DBMethod): Option[DBParam] = {
    val method_id = method.method_id
    db.withConnection{ conn =>
      implicit val a = conn
      val res = SQL(
        """SELECT * FROM method_param
           WHERE method_id = {method_id}
              AND param_position = {position};
        """).on('method_id -> method_id).on('position -> position).as(param_parse.*)
      res.map(a => a(method))
    } match{
      case Seq() => None
      case Seq(v) => Some(v)
      case _ => ???
    }
  }
  def varsFromCCallback(cmd : CallbackOrHole) : Seq[(String,DBParam)] = {
    if(cmd.cbCommand.isCallback) varsFromCCallback(cmd.getCallback) else Seq() //empty sequence for hole
  }
  def varsFromCCallback(callback : CCallback): Seq[(String, DBParam)] ={
    //Note can be multiple methods if not fully specified
    val methods = getMethod(callback)

    def protoParams2DBParam(a : Seq[Option[CParam]], loc : Symbol) =
      a.zipWithIndex flatMap { b => b match{
        case (Some(CParam(Param.Variable(CVariable(name)))), indexpos) =>
          val position: Int = if(loc == 'rec) 1 else if(loc=='ret) 0 else indexpos + 2
          methods.flatMap{ a =>
            getDBParam(position, a) match{
              case Some(v) =>
                Some(name,v)
              case None => None
            }
          }
        case _ => Seq[(String,DBParam)]()
        }
      }

    val retList: Seq[(String,DBParam)] = protoParams2DBParam(Seq(callback.returnValue), 'ret)
    val recList: Seq[(String, DBParam)] = protoParams2DBParam(Seq(callback.receiver), 'rec)
    val paramList: Seq[(String, DBParam)] = protoParams2DBParam(callback.parameters.map(a => Some(a)), 'param)

    val out: Seq[(String,DBParam)] =
      callback.nestedCommands.flatMap(varsFromCCallin) ++ retList ++ recList ++ paramList
    out
  }
  def varsFromCCallin( cmd : CCommand): Seq[(String,DBParam)] = {
    if(cmd.ciCommand.isCallin) {
      val callin = cmd.getCallin
      val methods = getMethod(callin)
      def protoParams2DBParam(a: Seq[CParam], loc : Symbol) =
        a.zipWithIndex flatMap { b =>
        b match {
          case (CParam(Param.Variable(CVariable(name))), indexpos) =>
            val position: Int = if(loc == 'rec) 1 else if(loc=='ret) 0 else indexpos + 2
            val a: Seq[(String, DBParam)] = methods.flatMap{ a =>
              getDBParam(position, a) match{
                case Some(v) => Some(name,v)
                case None => None
              }
            }
            a
          case _ => Seq[(String, DBParam)]()
        }
      }
      val retList = protoParams2DBParam(Seq(callin.getReturnValue), 'ret)
      val recList = protoParams2DBParam(Seq(callin.getReceiver), 'rec)
      val paramList = protoParams2DBParam(callin.parameters, 'param)

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
      val vars : Seq[(String, DBParam)] = (a.cbCommand.callback map varsFromCCallback).getOrElse(???)
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
      val varAttempt = a.cbCommand.callback map varsFromCCallback
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
          val r: Map[(Int, Int), Set[DBTrace]] = acc + (edge -> newEdges.union(oldSet))
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

  def getDBMethodFromId(param_id : Int): DBParam ={
    val param_parse=  {
      get[Int]("param_id") ~
        get[Int]("method_id") ~
        get[Int]("param_position") map {
        case param_id ~ method_id ~ param_position =>
          (param_id, param_position, method_id)
      }
    }
    val tup = db.withConnection{implicit conn =>
      val v = SQL("""SELECT * FROM method_param WHERE param_id = {id};""")
        .on('id -> param_id).as(param_parse.single)
      v
    }

    val dBMethod = db.withConnection{implicit conn =>
      SQL("""SELECT * FROM method WHERE method_id = {id}""")
        .on('id -> tup._3).as(method_id_parse.single)
    }
    DBParam(tup._1,tup._2,tup._3,dBMethod)

  }


  /**
    * search for completions to missing callbacks
    *
    * @param completion_query
    * @return
    */
  override def completionSearch(completion_query: CTrace, isCallback : Boolean): List[(Int,CallinOrCallback)] = {
    val traceToRank: Map[DBTrace, Int] = traceRankSearch(completion_query).toMap
    val methodsInQuery = completion_query.callbacks.flatMap(varsFromCCallback)
//    val everyPair = for( traceId <- traceIDs; method <- methodsInQuery)
//      yield (traceId,method)

    //TODO: query for method and one of the methods,
    // join together the method/var,
    // rank based on connections as well as trace score (multiply?)

    /**
      * parse out method and ranking generated from the relative trace
      */
    val parse_destination = {
      get[Int]("end_method_param") ~
      get[Int]("trace_id") map {
        case end_method_param ~ trace_id => (getDBMethodFromId(end_method_param), traceToRank(DBTrace(trace_id)))
      }
    }
    //create end_method_param X trace pairs based on start_method_param and convert them into dbparam X rank
    val param_rank_list: Seq[((String, DBParam), Int)] = db.withConnection{ implicit conn =>
      methodsInQuery.flatMap { a =>
        val list = (traceToRank.keys.map(_.trace_id).toList).mkString(",")
        //Get distinct methods that share data with methods in the query
        if (list.size > 0) {
          val q =
            s"""SELECT DISTINCT end_method_param, trace_id FROM trace_edge
            WHERE trace_id IN (${list})  AND start_method_param = {start};"""
          SQL(
            q) //TODO: sql exception may be here, was ({traces})
            //          .on('traces -> list)
            .on('start -> a._2.param_id)
            .as(parse_destination.*)
            .map(v => ((a._1, v._1), v._2)) //retain variable name
        }else Seq()
      }
    }.filter{ _._1._2.d.isCallback == isCallback}
    //sum the ranks for a given dbparam
    val accumulated_param_rank = param_rank_list.foldLeft(Map[(String,DBParam),Int]()){ (acc,v) =>
      val key: (String, DBParam) = v._1
      val rank: Int =v._2
      val oldval: Int = acc.getOrElse(v._1,0)
      acc + (key ->  (rank + oldval))
    }.toList

    //map from dbMethod to possible parameters and their rankings
    val method_to_params = accumulated_param_rank.foldLeft(Map[DBMethod, Set[(String,DBParam, Int)]]()){(acc,v) =>
      val rank: Int = v._2
      val varname: String = v._1._1
      val dbparam: DBParam = v._1._2
      val dbmethod = dbparam.d
      val oldSet: Set[(String, DBParam, Int)] = acc.getOrElse(dbmethod, Set[(String,DBParam, Int)]())
      acc + (dbmethod ->  (oldSet + ((varname, dbparam, rank))))
    }
    val out = method_to_params.foldLeft(List[(Int, CallinOrCallback)]()){ (acc,v) =>
      val method: DBMethod = v._1
      val params: Set[(String, DBParam, Int)] = v._2

      //mapping from position to varname and score
      val posmap: Map[Int, Set[(String, Int)]] =
        params.foldLeft(Map[Int, Set[(String,Int)]]()){ (acc, v) =>
          acc + (v._2.param_position -> (acc.getOrElse(v._2.param_position, Set()) + ((v._1, v._3))))}

      val paramsets = posmap.foldLeft(Set[Map[Int, (String, Int)]](Map())) { (acc, v) =>
        val position: Int = v._1
        val paramsAtPosition: Set[(String, Int)] = v._2
        paramsAtPosition.foldLeft(acc) { (acc2, v) =>
          acc.map(a => a + (position -> v)) ++ acc
        }
      }
      val method_completions: Set[(Int, CallinWrapper)] = paramsets.map { a =>
        if (isCallback) {
          ???
        } else {
          val paramKeys = a.keys.filter(a => a > 1)
          val hasParams = a.keys.exists( a => a > 1)
          val score = a.foldLeft(0){ (acc,v) => acc + v._2._2}
          (score,CallinWrapper(
            CCallin(
              methodSignature = method.signature,
              frameworkClass = method.firstFramework,
              returnValue = a.get(0).map(a => CParam().withVariable(CVariable(a._1))),
              receiver = a.get(1).map(a => CParam().withVariable(CVariable(a._1))),
              parameters = if(hasParams) (2 to (numParamsFromSig(method.signature)+1)).map{ b =>
                a.get(b) match{
                  case Some(v) => CParam().withVariable(CVariable(v._1))
                  case None => CParam().withPrHole(Hole(false))
                }
              } else Nil

            )
          ))
        }
      }
      acc ++ method_completions.toList.filter(a => a._1 > 0)
    }.sortWith( (a,b) => a._1 > b._1)
  out
  }
  def numParamsFromSig(sig : String): Int ={
//    sig.split("""\(""") match{
//      case h :: (n : String) :: nil => n.split(",").size
//      case _ => ???
//    }
    sig.split("""\(""")(1).split(",").length
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

  private def getMethod(sig: String, fmwkin: String, isCallback : Boolean) = {
    val fmwk = if(isCallback && !fmwkin.startsWith("class")) s"class ${fmwkin}" else fmwkin
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
        val res = SQL("""SELECT * FROM method_param WHERE method_id = {id}""")
          .on('id -> method.method_id).as(param_parse.*)
        res map (a => a(method))
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
    if(c.cbCommand.isCbHole){
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
    if(c.ciCommand.isCiHole){
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
