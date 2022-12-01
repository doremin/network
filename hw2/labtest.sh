#!/bin/bash

# input
rm -f a.out down_temp* output.txt
src=$1;

echo $1
echo $2

if [[ "$src" =~ ".cpp" ]];
then
	g++ $src
	./a.out $2 > output.txt &
elif [[ $src =~ ".c" ]];
then
	gcc $src 
	./a.out $2 > output.txt &
elif [[ $src =~ ".java" ]];
then
	javac $src
	sleep 1
	cname=$(ls HW2*.class | sed 's/.class//')
	java $cname $2 > output.txt &
elif [[ $src =~ ".py" ]];
then
	python3 $src $2 > output.txt &
else
	echo "not supported" $src
fi

sleep 1

wget -O down_temp_biga -t 2 -T 10 http://localhost:$2/biga.html
sleep 1
wget -O down_temp_a -t 2 -T 10 http://localhost:$2/a.html
sleep 1
wget -O down_temp_b -t 2 -T 10 http://localhost:$2/b.html
sleep 1
wget -O down_temp_pal -t 2 -T 10 http://localhost:$2/palladio.jpg

#killall -q a.out python3 java
killall -q a.out python3 java

succcnt=0
diff biga.html down_temp_biga
if [[ $? == 0 ]];
then
	let 'succcnt=succcnt+1'
fi
diff a.html down_temp_a
if [[ $? == 0 ]];
then
	let 'succcnt=succcnt+2'
fi
diff b.html down_temp_b
if [[ $? == 0 ]];
then
	let 'succcnt=succcnt+4'
fi

cmp palladio.jpg down_temp_pal
if [[ $? == 0 ]];
then
	let 'succcnt=succcnt+8'
fi
grep "User-Agent: Wget" output.txt
if [[ $? == 0 ]];
then
	let 'succcnt=succcnt+16'
fi
grep "5 headers" output.txt
if [[ $? == 0 ]];
then
	let 'succcnt=succcnt+32'
fi

# show the result
echo "Result: " $succcnt $src

