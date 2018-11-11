for f in $(cd $1; find $(pwd) -name "*.txt")
do
echo $f
done
