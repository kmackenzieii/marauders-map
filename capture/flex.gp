set cbrange [1:10]
set palette defined (1 "green", 2 "red", 3 "blue", 4 "yellow", 5 "orange", 6 "purple", 7 "black", 8 "grey", 9 "cyan", 10 "magenta" )
plot '<cat' using 1:2:3 with points palette
