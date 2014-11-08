#cat kirk_first_test_channel11.txt | awk '\
cat data.txt | awk '\
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
	print k, $3, j
	k=k+1
}'
