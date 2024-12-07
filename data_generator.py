import numpy as np
# Python program to create 
# a sorted list of unique random 
def createRandomSortedList(num, start = 1, end = 100):
    arr = np.random.choice(np.arange(start, end + 1), size=num, replace=False)
    return arr

if __name__ == "__main__":
    args = input("Enter the number of elements: ")
    num = int(args)
    list = createRandomSortedList(num, 1, num)
    print(list)