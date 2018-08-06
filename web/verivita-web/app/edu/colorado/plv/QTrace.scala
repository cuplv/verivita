package edu.colorado.plv


/**
  * Trace query, can also be used to represent a query
  */
class QTrace(callbacks: List[QCallback]){

}

object QTrace {

}



/**
  * represents a specific matcher for a method or a "contains"
  */


abstract class QType
/**
  * object in the android framework
  * @param name name of the object, "e.g. android.os.AsyncTask"
  */
case class QObject(name : String) extends QType
case class QPrimInt() extends QType
case class QPrimFloat() extends QType

/**
  *
  * @param selected when this hole is the one being searched for
  *                 note only one hole can be selected at a time
  */
case class QTypeHole(selected : Boolean)


abstract class QMethodIdentifier
case class ConcreteMethod(sig: String) extends QMethodIdentifier
/**
  *
  * @param name simple name of class, e.g. "onCreate"
  * @param clazz class of method
  * @param params parameter types that must be in query method
  */
case class MethodQuery(name : Option[String], clazz : Option[QType],
                       params : Set[QType], returnVal : QType) extends QMethodIdentifier

case class QCallback(ident: QMethodIdentifier, cmds : List[QCmd])


abstract class QCmd
case class QInvoke(callin: QCallin)
case class QCmdHole(selected : Boolean)

case class QCallin(ident: QMethodIdentifier)




