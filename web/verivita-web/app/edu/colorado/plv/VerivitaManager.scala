package edu.colorado.plv

import java.io.File
import java.util
import java.util.concurrent.Executors

import javax.inject.Inject
import jep.Jep
import play.Environment

import scala.collection.{JavaConverters, immutable}
import scala.concurrent.{Await, ExecutionContext, Future}
import scala.concurrent.duration._
import scala.io.{BufferedSource, Source}

object VerivitaManager{
  var count = 0
}

class VerivitaManager @Inject()(env: Environment) extends TraceManager{
  VerivitaManager.count = VerivitaManager.count + 1
  if(VerivitaManager.count > 1) throw new IllegalStateException("Only one instance of VerivitaManager allowed")
  val fileList = getListOfFiles()
  val filePaths = fileList.map(a => a.getAbsolutePath)
  val nametopath = fileList.map(a => (a.getName-> a.getAbsolutePath)).toMap


  implicit val ec = new ExecutionContext {
    val threadPool = Executors.newFixedThreadPool(1);

    def execute(runnable: Runnable) {
      threadPool.submit(runnable)
    }

    def reportFailure(t: Throwable) {}
  }
  val jepFuture: Future[Jep] = Future{
    val tid = Thread.currentThread().getId()
    val jep = new Jep(false)
    jep.eval("import sys")
    println(jep.getValue("sys.version"))
    jep
  }
  val jep: Jep = Await.result(jepFuture, 999 seconds)

  def jepRun[T](task : Jep => T): T ={
    val f = Future{
      task(jep)
    }
    Await.result(f, 9999 seconds)
  }
//  def jepEval(cmd : String) = {
//    val f = Future{
//      jep.eval(cmd)
//    }
//    Await.result(f,999 seconds)
//  }
//  def jepGetVal(cmd : String) ={
//    val f =  Future{
//      jep.getValue(cmd)
//    }
//    Await.result(f, 999 seconds)
//  }

  jepRun((jep: Jep) => {
    jep.eval("import driver")
    jep.eval("import traces.ctrace")
  })
  //TODO: jep.close on object destruction
  //TODO: notes perhaps serializing trace to json can make interface more stable
  def getSpecList(file: String): String = {
    val bufferedSource: BufferedSource = Source.fromFile(env.getFile(file))
    val specList : List[String] = bufferedSource.getLines().toList
    bufferedSource.close()
    specList.map(a => "'" + a + "'").mkString(",")
  }
  def createDriver(jep: Jep, tracePath : String, simplifyTrace: Boolean) = {
    var debug = "False"
    var filter_msg= "None"
    val strSimplifyTrace = if (simplifyTrace) "True" else "False"

//    jep.runScript("/Users/s/foo.py")
//    val value = jep.getValue("exception")

    val specListFile = s"conf/speclists/va1.txt"
    //TODO: get spec file list from somewhere

    val specString = getSpecList(specListFile)
    val disallowString = getSpecList("conf/speclists/AlertDialog.dismiss.txt")
    val specfileList = s"""[${specString},${disallowString}]"""
    jep.eval(s"""spec_file_list = $specfileList""")
    jep.eval(s"""driver_opts = driver.DriverOptions("${tracePath}","bin",spec_file_list,${strSimplifyTrace},${debug},${filter_msg},True)""")
    jep.eval("idriver = driver.Driver(driver_opts)")
  }
  def cleanUpDriver(jep: Jep) = {
    jep.eval("del spec_file_list")
    jep.eval("del driver_opts")
    jep.eval("del idriver")
  }

  def getCmsg(jep: Jep, expr: String): TraceMessage = {
    val direct = MsgBack
    val isCallback = jep.getValue(s"isinstance(${expr}, driver.CCallback)").asInstanceOf[Boolean]
    val isCallin = jep.getValue(s"isinstance(${expr}, driver.CCallin)").asInstanceOf[Boolean]
    val isException = jep.getValue(s"isinstance(${expr}, driver.CMessage)").asInstanceOf[Boolean]
    val name = jep.getValue(s"${expr}.method_name").asInstanceOf[String]
    val clazz = jep.getValue(s"${expr}.class_name").asInstanceOf[String]
    val pkg = ""
    val method = Some(MethodIdentifier(name, clazz, pkg))
    val cicb = if(isCallback) Callback else Callin
    TraceMessage(direct, cicb,method)
  }
  def getTraceFromVV(path : String) = {
    val t = (jep: Jep) => {
      createDriver(jep,path, false)
      val traceexpr = "idriver.trace"
      val traceLen: Int = jep.getValue(s"len(${traceexpr}.children)").asInstanceOf[Integer]
      val result = (0 until traceLen).map(i => {
        getCmsg(jep, s"idriver.trace.children[${i}]")
      })
      cleanUpDriver(jep)
      result
    }
    jepRun(t).toList
  }
  def verifyTraceFromVV(fname : String) = {
    val path = nametopath(fname)
    jepRun( (jep: Jep) => {
      createDriver(jep,path,true)
      val nuxmvpath = sys.env("NUXMV_PATH")
      //(res, cex, mapback)
      val runcmd = s"""res = idriver.run_ic3('${nuxmvpath}', 40)"""
      jep.eval(runcmd)
      //TODO: extract cex
      val cex = List[TraceMessage]()
//      List("cex","res","mapback") map (a => jep.getValue(s"del ${a}"))
      jep.eval("del res")
      cex
    })
  }


  override def verifyTrace(traceId: String, disallowId: String): List[TraceMessage] = verifyTraceFromVV(traceId)

  override def getTrace(id: String): List[TraceMessage] = {
//    val maybeString = sys.env.get("DYLD_LIBRARY_PATH")
//    val jep: Jep = new Jep()
//    jep.runScript("/Users/s/foo.py")
//    jep.eval("ans = foo()")
//    val a : PyJObject = ???
//    val value2 = jep.getValue("foo()")
//    val value: AnyRef = jep.getValue("ans")
    val tracepath = filePaths.filter(a => a.contains(id)).headOption

//    val tracepath = sys.env("TRACE_PATH")

    println(tracepath)
    getTraceFromVV(tracepath.getOrElse(???))
  }
  def getListOfFiles():List[File] = {
    val dir = sys.env("TRACE_DIR")
    val d = new File(dir)
    if (d.exists && d.isDirectory) {
      d.listFiles.filter(_.isFile).toList
    } else {
      List[File]()
    }
  }

  override def getTraceList(): List[String] = {
    fileList.map(a => a.getName)
  }

  override def finalize(): Unit = {
    super.finalize()
    jep.close()
  }
}
