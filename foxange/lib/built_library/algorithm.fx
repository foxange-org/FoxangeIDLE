def len(arg):
	let str temp = str(arg)
	let int value = 0
	for i in temp:
		value += 1
	return value
def range(int start =0, int end, int step=1)->list:
	let int i = start
	let list<int> values = []
	while i<=end:
		values.append(i)
		i+=step
	return values
