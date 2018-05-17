import com.google.inject.AbstractModule
import java.time.Clock

import com.google.inject.name.Names
import edu.colorado.plv.{FakeManager, TraceManager, VerivitaManager}
import services.{AtomicCounter, Counter}


/**
 * This class is a Guice module that tells Guice how to bind several
 * different types. This Guice module is created when the Play
 * application starts.

 * Play will automatically use any class called `Module` that is in
 * the root package. You can create modules in other locations by
 * adding `play.modules.enabled` settings to the `application.conf`
 * configuration file.
 */
class Module extends AbstractModule {

  override def configure() = {
    // Set AtomicCounter as the implementation for Counter.
    bind(classOf[Counter]).to(classOf[AtomicCounter])
    println("===binding classes")
    sys.env.get("VERIVITA_MOCK") match{
      case Some("true") => {
        println("===fake manager")
        bind(classOf[TraceManager]).to(classOf[FakeManager])
      }
      case _ => {
        println("===real manager")
        bind(classOf[TraceManager]).to(classOf[VerivitaManager])
      }
    }

  }

}
