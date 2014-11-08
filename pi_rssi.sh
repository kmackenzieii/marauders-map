sshpass -p "raspberry" scp pi@192.168.43.170:/home/pi/Desktop/RSSI/data.txt data.txt
cat data.txt\
        | awk '\
BEGIN{
	k=0
}
{
	flag=0
	j=0
	for(x in used){
		j++
		if(used[x] == $1){
			flag=1
			break
		}
	}
	if(!flag){
		j=j+1
		used[j]=$1
	}
	if($1 == $2){
	        print k, $3, j
	}
	k=k+1
}' > capture.txt
gnuplot -persist plot.gp &
while true; do
sshpass -p "raspberry" scp pi@192.168.43.170:/home/pi/Desktop/RSSI/data.txt data.txt
cat data.txt\
	| awk '\
BEGIN{
	k=0
}
{
	flag=0
	j=0
	for(x in used){
		j++
		if(used[x] == $1){
			flag=1
			break
		}
	}
	if(!flag){
		j=j+1
		used[j]=$1
	}
	if($1 == $2){
	        print k, $3, j
	}
	k=k+1
}' > capture.txt
done
