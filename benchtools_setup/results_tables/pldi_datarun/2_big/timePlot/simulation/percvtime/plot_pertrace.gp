#set size square
#set size 0.53,0.66
set size 1,1
set xrange [10:3600]
set yrange [1:105]
set logscale x
unset logscale y

#set key right bottom box
#set key left top
unset key
set xlabel 'Time Budget Per Trace (seconds)'
set ylabel 'Validated Traces (%)'
set title ''
set terminal postscript eps color
set arrow from 360, graph 0 to 360, graph 1 nohead 
set label '6 minutes' at 340, graph 0.5 rotate
#graph is [0,1] representing absolute position on graph, first indicates the coordinates on axes
set arrow from graph 0, first 92.0 to graph 1, first 92.0 nohead 
set label 'Over 92% of traces validated' at  graph 0.2,first 94.0
set output '| epstopdf --filter > accumulated_time_big_sim_exp.pdf'
plot \
     'sim_perc_timelifestate.data' using 2:1 with linespoints lw 3 lt 1 pt 1 title 'Lifestate'
