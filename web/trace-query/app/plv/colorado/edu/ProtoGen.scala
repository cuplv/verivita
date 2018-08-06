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

  def q1 = {
    val callbacks = List(
      CallbackOrHole().withCallback(
        CCallback(
          methodSignature = "void onCreate(android.os.Bundle)",
          receiver = "a", nestedCommands = Seq(
            CCommand().withCallin(CCallin(methodSignature = ""))
          )))
    )
    val identifier = Some(TraceIdentifier(appName = "test"))
    val a = CTrace(id = identifier, callbacks = callbacks)
    JsonFormat.toJsonString(a)
  }
  def main(args: Array[String]): Unit = {
    println("q1")
    println(q1)
  }
}
