name := "play-elm-example"

version := "1.0-SNAPSHOT"

lazy val root = (project in file(".")).enablePlugins(PlayScala)

scalaVersion := "2.12.5"

libraryDependencies ++= Seq(
  guice,
  "org.scalatestplus.play" %% "scalatestplus-play" % "3.1.2" % Test,
  "black.ninia" % "jep" % "3.7.1"
)
(ElmKeys.elmOptions in ElmKeys.elmMake in Assets) ++= Seq("--debug")

