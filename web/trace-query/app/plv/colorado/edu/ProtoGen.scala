package plv.colorado.edu

import edu.colorado.plv.QueryTrace._
import scalapb.json4s.JsonFormat

object ProtoGen {

  /**
    * implicit conversion of strings to variable names
    * @param varname
    * @return
    */
  implicit def string2CParam(varname : String): Option[CParam] = {
    val value = CParam().withVariable(CVariable(varname))
    Some(value)
  }

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
          nestedCommands = Seq(
            CCommand().withCallin(CCallin(methodSignature = "java.lang.Object getSystemService(java.lang.String)",
              frameworkClass = "java.lang.Object android.app.Activity.getSystemService(java.lang.String)",
              receiver = "a")),
            CCommand().withCallin(CCallin(methodSignature = "android.view.View findViewById(int)",
              frameworkClass = "android.view.View android.app.Activity.findViewById(int)",
              receiver = "a"
            )),
            CCommand().withHole(Hole(true))
          )
        )
      ),
      CallbackOrHole().withHole(Hole(false))
    )
    ctraceFromCallbacks(callbacks)
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
