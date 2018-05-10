#set size square
#set size 0.53,0.66
set size 1,1
set xrange [-2:100]
set yrange [0.01:100]
set logscale y

#set key right bottom box
#set key left top
set key off
set xlabel 'Total Traces Validated (%)'
set ylabel 'Cumulative Time (hours)'
set title ''
set terminal postscript eps color
set output '| epstopdf --filter > cumulative_trace_time_big_sim_exp.pdf'
plot \
     'sim_perc_timecumulative_lifestate.data' using 1:2 with linespoints lw 3 lt 1 pt 1
