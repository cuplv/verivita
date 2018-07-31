import com.google.inject.AbstractModule
import plv.colorado.edu.{PostgresTraceDbQuery, TraceDbQuery}

class Module extends AbstractModule {

  override def configure() = {
    // Set AtomicCounter as the implementation for Counter.

    bind(classOf[TraceDbQuery]).to(classOf[PostgresTraceDbQuery])


  }

}
