#set size square
#set size 0.53,0.66
set size 1,1
set xrange [0.1:10500]
set yrange [1:85]
set logscale x

#set key right bottom box
set key left top
set xlabel 'Total time'
set ylabel 'Number of solved instances'
set title ''
set terminal postscript eps color
set output '| epstopdf --filter > cav12-accumulated.pdf'
plot \
     'cav12-accumulated.ia.time.data' using 3:0 with linespoints lw 3 lt 1 pt 1 title 'IC3-IA' , \
     'cav12-accumulated.conc.time.data' using 3:0 with linespoints lw 3 lt 2 pt 2 title 'IC3-QE', \
     'cav12-accumulated.z3.time.data' using 3:0 with linespoints lw 3 lt 3 pt 3 title 'Z3', \
     'cav12-accumulated.ctigar.time.data' using 3:0 with linespoints lw 3 lt 7 pt 7 title 'CTIGAR-REIMPL'
