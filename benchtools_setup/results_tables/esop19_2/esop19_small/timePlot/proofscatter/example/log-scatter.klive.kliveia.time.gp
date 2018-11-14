set size square
set xrange [0.05:1200.0]
set yrange [0.05:1200.0]
set key off
set logscale x
set logscale y
set terminal postscript eps color size 3,3
set output '| epstopdf --filter > log-scatter.klive.kliveia.time.pdf'

plot x notitle lt -1, 10*x notitle lt -1, x/10 notitle lt -1, \
'log-scatter.klive.kliveia.time.data' using ($2==0 ? $3 : -1):($2==0 ? $4 : -1) title 'safe' with points pointtype 5 lt 3, \
'log-scatter.klive.kliveia.time.data' using ($2==1 ? $3 : -1):($2==1 ? $4 : -1) title 'unsafe' with points pointtype 7 lt 1

