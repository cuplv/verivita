package plv.colorado.edu

object Utils {
  def power[A](t: Set[A]): Set[Set[A]] = {
    @annotation.tailrec
    def pwr(t: Set[A], ps: Set[Set[A]]): Set[Set[A]] =
      if (t.isEmpty) ps
      else pwr(t.tail, ps ++ (ps map (_ + t.head)))

    pwr(t, Set(Set.empty[A])) //Powerset of ∅ is {∅}
  }
}
