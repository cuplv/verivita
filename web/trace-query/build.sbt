name := """trace-query"""
organization := "plv.colorado.edu"

version := "1.0-SNAPSHOT"

lazy val root = (project in file(".")).enablePlugins(PlayScala)

scalaVersion := "2.12.6"

//PB.targets in Compile := Seq(
//  scalapb.gen() -> (sourceManaged in Compile).value
//)

libraryDependencies += guice
libraryDependencies += jdbc
libraryDependencies += "org.scalatestplus.play" %% "scalatestplus-play" % "3.1.2" % Test
//libraryDependencies += "com.thesamet.scalapb" %% "scalapb-runtime" % "0.7.1"
//libraryDependencies += "com.trueaccord.scalapb" %% "scalapb-json4s" % "0.7.1"
libraryDependencies += "edu.colorado.plv" %% "trace-serializer" % "0.1.0-SNAPSHOT"
//libraryDependencies += "org.postgresql" % "postgresql" % "9.3-1102-jdbc4"
libraryDependencies += "org.postgresql" % "postgresql" % "42.2.4"



