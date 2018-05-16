package edu.colorado.plv

import java.util
import java.util.concurrent.Executors

import jep.Jep

import scala.collection.{JavaConverters, immutable}
import scala.concurrent.{Await, ExecutionContext, Future}
import scala.concurrent.duration._

class VerivitaManager extends TraceManager{
  implicit val ec = new ExecutionContext {
    val threadPool = Executors.newFixedThreadPool(1);

    def execute(runnable: Runnable) {
      threadPool.submit(runnable)
    }

    def reportFailure(t: Throwable) {}
  }
  val jepFuture: Future[Jep] = Future{
    val tid = Thread.currentThread().getId()
    new Jep(false)
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

  def createDriver(jep: Jep, tracePath : String, simplifyTrace: Boolean) = {
    var debug = "False"
    var filter_msg= "None"
    val strSimplifyTrace = if (simplifyTrace) "True" else "False"

//    jep.runScript("/Users/s/foo.py")
//    val value = jep.getValue("exception")

    //TODO: get spec file list from somewhere
    jep.eval("""spec_file_list = ["/Users/s/Documents/source/callback-verification/cbverifier/android_specs/enabledisable/android.os.CountdownTimer/countdowntimer.spec"]""")
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
      val traceLen: Int = jep.getValue("len(idriver.trace.children)").asInstanceOf[Integer]
      val result = (0 until traceLen).map(i => {
        getCmsg(jep, s"idriver.trace.children[${i}]")
      })
      cleanUpDriver(jep)
      result
    }
    jepRun(t).toList

  }


  override def verifyTrace(traceId: String, disallowId: String): List[TraceMessage] = List()

  override def getTrace(id: String): List[TraceMessage] = {
//    val maybeString = sys.env.get("DYLD_LIBRARY_PATH")
//    val jep: Jep = new Jep()
//    jep.runScript("/Users/s/foo.py")
//    jep.eval("ans = foo()")
//    val a : PyJObject = ???
//    val value2 = jep.getValue("foo()")
//    val value: AnyRef = jep.getValue("ans")
    getTraceFromVV(sys.env("TRACE_PATH"))
  }

  override def getTraceList(): List[String] = List()

  override def finalize(): Unit = {
    super.finalize()
    jep.close()
  }
}
