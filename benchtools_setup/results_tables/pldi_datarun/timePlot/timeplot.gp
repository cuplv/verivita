#set size square
#set size 0.53,0.66
set size 1,1
set xrange [1:18000]
set yrange [1:100]
set logscale x

#set key right bottom box
set key left top
set xlabel 'Total Time (seconds)'
set ylabel 'Processed (traces)'
set title ''
set terminal postscript eps color
set output '| epstopdf --filter > accumulated_time_small_exp.pdf'
plot \
     'just_disallow.data' using 3:0 with linespoints lw 3 lt 1 pt 1 title 'disallowable' , \
     'lifecycle.data' using 3:0 with linespoints lw 3 lt 2 pt 2 title 'lifecycle', \
     'lifestate_va0.data' using 3:0 with linespoints lw 3 lt 3 pt 3 title 'lifestate no attach', \
     'lifestate_va1.data' using 3:0 with linespoints lw 3 lt 6 pt 7 title 'lifestate'

#http://knowyourmeme.com/memes/these-companies-test-on-animals
