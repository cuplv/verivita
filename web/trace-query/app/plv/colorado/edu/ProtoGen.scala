package plv.colorado.edu

import edu.colorado.plv.QueryTrace._
import scalapb.json4s.JsonFormat

object ProtoGen {

  /**
    * implicit conversion of strings to variable names
    * @param varname
    * @return
    */
  implicit def string2OCParam(varname : String): Option[CParam] = {
    val value = CParam().withVariable(CVariable(varname))
    Some(value)
  }
  implicit def string2CParam(varname : String) : CParam = CParam().withVariable(CVariable(varname))


  def ctraceFromCallbacks(callbacks : List[CallbackOrHole]) = {
    val identifier = Some(TraceIdentifier(appName = "test"))
    val a = CTrace(id = identifier, callbacks = callbacks)
    JsonFormat.toJsonString(a)
  }
  def q1 = {
    val callbacks = List(
      CallbackOrHole().withCallback(
        CCallback(
          methodSignature = "void onCreate(android.os.Bundle)",
          firstFrameworkOverrrideClass = "class void android.app.Activity.onCreate(android.os.Bundle)",
          receiver = "a",
          nestedCommands = Seq(
            CCommand().withCallin(CCallin(methodSignature = "java.lang.Object getSystemService(java.lang.String)",
              frameworkClass = "java.lang.Object android.app.Activity.getSystemService(java.lang.String)",
              receiver = "a"))
          )
        ))
    )
    ctraceFromCallbacks(callbacks)

  }
  def q2 = {
    val callbacks = List(
      CallbackOrHole().withCallback(
        CCallback(
          methodSignature = "void onCreate(android.os.Bundle)",
          firstFrameworkOverrrideClass = "class void android.app.Activity.onCreate(android.os.Bundle)",
          receiver = "a",
          parameters = Seq("b"),
          nestedCommands = Seq(
            CCommand().withCallin(CCallin(methodSignature = "java.lang.Object getSystemService(java.lang.String)",
              frameworkClass = "java.lang.Object android.app.Activity.getSystemService(java.lang.String)",
              receiver = "a")),
            CCommand().withCallin(CCallin(methodSignature = "android.view.View findViewById(int)",
              frameworkClass = "android.view.View android.app.Activity.findViewById(int)",
              receiver = "a"
            ))

          )
        ))
    )
    ctraceFromCallbacks(callbacks)

  }
  def q_with_hole = {
    val callbacks = List(
      CallbackOrHole().withCallback(
        CCallback(
          methodSignature = "void onCreate(android.os.Bundle)",
          firstFrameworkOverrrideClass = "class void android.app.Activity.onCreate(android.os.Bundle)",
          receiver = "a",
          parameters = Seq("b"),
          nestedCommands = Seq(
            CCommand().withCallin(CCallin(methodSignature = "java.lang.Object getSystemService(java.lang.String)",
              frameworkClass = "java.lang.Object android.app.Activity.getSystemService(java.lang.String)",
              receiver = "a")),
            CCommand().withCallin(CCallin(methodSignature = "android.view.View findViewById(int)",
              frameworkClass = "android.view.View android.app.Activity.findViewById(int)",
              receiver = "a"
            )),
            CCommand().withCiHole(Hole(true))
          )
        )
      ),
      CallbackOrHole().withCbHole(Hole(false))
    )
    ctraceFromCallbacks(callbacks)
  }
  def singleCallin = {
    val c = CCommand().withCallin(CCallin(methodSignature = "java.lang.Object getSystemService(java.lang.String)",
        frameworkClass = "java.lang.Object android.app.Activity.getSystemService(java.lang.String)",
        receiver = "a",
        returnValue = "b"
      )
      )
    JsonFormat.toJsonString(c)
  }
  def singleCmdHole = {
    val c = CCommand().withCiHole(Hole(false))
    JsonFormat.toJsonString(c)
  }
  def main(args: Array[String]): Unit = {
    println("q1")
    println(q1)
    println("q2")
    println(q2)
    println("q_withcallin_hole")
    println(q_with_hole)
  }
}
