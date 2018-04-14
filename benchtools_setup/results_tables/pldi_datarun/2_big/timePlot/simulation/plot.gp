#set size square
#set size 0.53,0.66
set size 1,1
set xrange [1:3600]
set yrange [1:2600]
set logscale x

#set key right bottom box
set key left top
set xlabel 'Total time (seconds)'
set ylabel 'Simulated Traces'
set title ''
set terminal postscript eps color
set output '| epstopdf --filter > accumulated_time_small_exp.pdf'
plot \
     'simtime.datalifecycle.data' using 3:0 with linespoints lw 3 lt 7 pt 7 title 'Lifecycle', \
     'simtime.datalifestate.data' using 3:0 with linespoints lw 3 lt 1 pt 1 title 'Lifestate'
