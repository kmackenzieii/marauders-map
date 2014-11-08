set key off
set border 3
set yzeroaxis
set cbrange [1:10]
set palette defined (1 "green", 2 "red", 3 "blue", 4 "yellow", 5 "orange", 6 "purple", 7 "black", 8 "grey", 9 "cyan", 10 "magenta" )
# Add a vertical dotted line at x=0 to show centre (mean) of distribution.
set yzeroaxis

# Each bar is half the (visual) width of its x-range.
set boxwidth 2 absolute
set style fill solid 1.0 noborder

bin_width = 0.1;

bin_number(x) = floor(x/bin_width)

rounded(x) = bin_width * ( bin_number(x) + 0.5 )

plot 'capture.txt' using 1:2:3 with points palette
#plot 'capture.txt' using (rounded($2)):(2) smooth frequency with boxes
pause 1
replot
reread
