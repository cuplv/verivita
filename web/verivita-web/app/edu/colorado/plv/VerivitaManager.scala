package edu.colorado.plv

import java.util

import jep.Jep

import scala.collection.JavaConverters

class VerivitaManager extends TraceManager{

  def createDriver(jep: Jep, tracePath : String, simplifyTrace: Boolean) = {
    var debug = "False"
    var filter_msg= "None"
    val strSimplifyTrace = if (simplifyTrace) "True" else "False"

//    jep.runScript("/Users/s/foo.py")
//    val value = jep.getValue("exception")
    jep.eval("import driver")
    //TODO: get spec file list from somewhere
//    jep.eval("""spec_file_list = ["/Users/s/Documents/source/callback-verification/cbverifier/android_specs/enabledisable/android.os.CountdownTimer/countdowntimer.spec"]""")
//    jep.eval(s"""driver_opts = driver.DriverOptions("${tracePath}","bin",spec_file_list,${strSimplifyTrace},${debug},${filter_msg},True)""")
  }

  def delStupidPythonVars(jep : Jep): Unit ={
    val vars = jep.getValue("vars().keys()")
    vars match {
      case a : util.ArrayList[String] => JavaConverters.collectionAsScalaIterable(a).filter(a => !a.contains("__")).map( (a: String) => jep.eval(s"del ${a}"))
    }
  }
  def getTraceFromVV(path : String) = {
    var jep : Jep = null //Jep initializes session in constructor
    try {
      jep = new Jep(false)
//      jep.eval("import driver")
      createDriver(jep, "/Users/s/Documents/data/callbacks-data_extracted/cleaned_traces/monkey_traces/_traces/nextgis-nextgislogger-app/monkeyTraces/trace-app-debug_2017-04-25_22:34:32.repaired", false)
    }finally {
      if(jep != null)
        delStupidPythonVars(jep)

        jep.close()

    }
    2

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
    getTraceFromVV("")
    List()
  }

  override def getTraceList(): List[String] = List()
}
