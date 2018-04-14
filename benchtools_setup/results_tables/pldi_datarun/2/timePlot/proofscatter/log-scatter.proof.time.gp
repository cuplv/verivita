set size square
set xrange [10:1000]
set yrange [10:1000]
set key off
set logscale x
set logscale y
set xlabel 'Lifecycle time (seconds)'
set ylabel 'Lifestate time (seconds)'
set terminal postscript eps color size 3,3
set output '| epstopdf --filter > log-scatter.proof.time.pdf'

plot x notitle lt -1, 10*x notitle lt -1, x/10 notitle lt -1, \
'proof.data' using ($2==0 ? $3 : -1):($2==0 ? $4 : -1) title 'safe' with points pointtype 5 lt 3, \
'proof.data' using ($2==1 ? $3 : -1):($2==1 ? $4 : -1) title 'unsafe' with points pointtype 7 lt 1

