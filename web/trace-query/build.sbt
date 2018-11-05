name := """trace-query"""
organization := "plv.colorado.edu"

version := "1.0-SNAPSHOT"

lazy val root = (project in file(".")).enablePlugins(PlayScala)

scalaVersion := "2.12.6"

//PB.targets in Compile := Seq(
//  scalapb.gen() -> (sourceManaged in Compile).value
//)

resolvers += "clojars" at "https://clojars.org/repo"
resolvers += "Local Maven Repository" at "file://"+Path.userHome.absolutePath+"/.m2/repository"

libraryDependencies ++= Seq(
  guice,
  jdbc,
  jdbc % Test,
  "org.scalatestplus.play" %% "scalatestplus-play" % "3.1.2" % Test,
  "edu.colorado.plv" %% "trace-serializer" % "0.1.0-SNAPSHOT",
  "org.postgresql" % "postgresql" % "42.2.4",
  "org.playframework.anorm" %% "anorm" % "2.6.2",
  "org.clojure" % "clojure" % "1.5.1",
  "anglican" % "anglican" % "1.0.0",
  "my-stuff" % "my-stuff" % "0.1.0-SNAPSHOT"
)
//libraryDependencies += "com.thesamet.scalapb" %% "scalapb-runtime" % "0.7.1"
//libraryDependencies += "com.trueaccord.scalapb" %% "scalapb-json4s" % "0.7.1"
//libraryDependencies += "org.postgresql" % "postgresql" % "9.3-1102-jdbc4"