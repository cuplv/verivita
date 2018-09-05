name := "vvweb"

version := "1.0-SNAPSHOT"

lazy val root = (project in file(".")).enablePlugins(PlayScala)

scalaVersion := "2.12.5"

//Note: protobuf stuff moved to trace-serializer project
libraryDependencies ++= Seq(
  guice,
  "org.scalatestplus.play" %% "scalatestplus-play" % "3.1.2" % Test,
  "edu.colorado.plv" %% "trace-serializer" % "0.1.0-SNAPSHOT",
  filters,
  ws
)
//(ElmKeys.elmOptions in ElmKeys.elmMake in Assets) ++= Seq("--debug")

//PB.targets in Compile := Seq(
//  scalapb.gen() -> (sourceManaged in Compile).value
//)



//lazy val vers = taskKey[Unit]("Prints 'scalapb version'")
//vers := println("scala pb version")
//vers := println(com.trueaccord.scalapb.compiler.Version.scalapbVersion)