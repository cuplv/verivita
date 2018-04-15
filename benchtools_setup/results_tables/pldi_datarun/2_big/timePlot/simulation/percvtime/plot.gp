#set size square
#set size 0.53,0.66
set size 1,1
set xrange [1:3600]
set yrange [1:105]
set logscale x

#set key right bottom box
set key left top
set xlabel 'Time Budget Per Trace (seconds)'
set ylabel 'Simulated Traces (%)'
set title ''
set terminal postscript eps color
set output '| epstopdf --filter > accumulated_time_big_sim_exp.pdf'
plot \
     'sim_perc_timelifestate.data' using 2:1 with linespoints lw 3 lt 1 pt 1 title 'Lifestate'
