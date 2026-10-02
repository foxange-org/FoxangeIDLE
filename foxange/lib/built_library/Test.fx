def test_for():
	print("[Debug] test value [1,2,3,4,5]")
	print("[Will] will print '1 2 3 4 5'")
	let list<int> values = [1,2,3,4,5]
	for value in values:
		print(value , end = ' ')
def test_print():
	print("[Debug] test value to print (1)")
	print("[Will] will print 1")
	print(1)
	print("[Debug] test value to print (1,end='test')")
	print("[Will] will print 1test")
	print(1,end="test")
def test_input():
	print("[Debug] test input (’>‘)")
	print("[Will] will print your input value")
	print(input(">"))
def test_while():
	print("[Debug] test i<=5")
	print("[Will] will print 1 2 3 4 5")
	let int i = 1
	while i<=5:
		print(i , end = ' ' )
		i = i + 1
	print()

@define PI 3.14
@define MSG "hello"
@define MAX(a, b) (a > b) ? a : b
@appendToken def fn

def test_preprocessor():
	print("[Debug] test @define PI 3.14")
	print("[Will] will print 3.14")
	print(PI)
	print("[Debug] test @define MSG 'hello'")
	print("[Will] will print hello")
	print(MSG)
	print("[Debug] test @define MAX(a, b) (a > b) ? a : b")
	print("[Will] will print 8")
	print(MAX(3, 8))

fn test_append_token():
	print("[Debug] test @appendToken def fn")
	print("[Will] will print 'fn works'")
	print("fn works")