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

  def main(args: Array[String]): Unit = {
    val callbacks = List(
      CCallback(methodSignature = "onCreate", receiver = "a")
    )
    val identifier = Some(TraceIdentifier(appName = "test"))
    val a = CTrace(id = identifier, callbacks = callbacks)
    println(JsonFormat.toJsonString(a))
  }
}
