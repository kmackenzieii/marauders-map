cat data.txt\
        | awk 'BEGIN{i=0}{if($1 == $2) print i,"\t", $3; i=i+0.1}' > first_test_capture.txt
gnuplot -persist first_test.gp
