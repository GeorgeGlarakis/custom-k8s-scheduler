# Python3 program for Bubble Sort Algorithm Implementation
# Time Complexity: O(n^2)
# Space Complexity: O(1)
def bubbleSort(arr):
    
    n = len(arr)

    # For loop to traverse through all 
    # element in an array
    for i in range(n):
        for j in range(0, n - i - 1):
            
            # Range of the array is from 0 to n-i-1
            # Swap the elements if the element found 
            #is greater than the adjacent element
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
                
    return arr

# Selection Sort algorithm in Python
# Time Complexity: O(n^2)
# Space Complexity: O(1)
def selectionSort(array, size):
    
    for s in range(size):
        min_idx = s
        
        for i in range(s + 1, size):
            
            # For sorting in descending order
            # for minimum element in each loop
            if array[i] < array[min_idx]:
                min_idx = i

        # Arranging min at the correct position
        (array[s], array[min_idx]) = (array[min_idx], array[s])

    return array

# Creating a function for insertion sort algorithm
# Time Complexity: O(n^2)
# Space Complexity: O(1)
def insertion_sort(arr):  
  
    # Outer loop to traverse on len(arr)  
    for i in range(1, len(arr)):  

        a = arr[i]  

        # Move elements of arr[0 to i-1], 
        # which are greater to one position
        # ahead of their current position  
        j = i - 1  
        
        while j >= 0 and a < arr[j]:  
            arr[j + 1] = arr[j]  
            j -= 1  
            
        arr[j + 1] = a  
        
    return arr  

# Creating a function for merge sort algorithm
# Time Complexity: O(n*log(n))
# Space Complexity: O(log(n))
def merge(arr, left, mid, right):
    n1 = mid - left + 1
    n2 = right - mid

    # Create temp arrays
    L = [0] * n1
    R = [0] * n2

    # Copy data to temp arrays L[] and R[]
    for i in range(n1):
        L[i] = arr[left + i]
    for j in range(n2):
        R[j] = arr[mid + 1 + j]

    i = 0  # Initial index of first subarray
    j = 0  # Initial index of second subarray
    k = left  # Initial index of merged subarray

    # Merge the temp arrays back
    # into arr[left..right]
    while i < n1 and j < n2:
        if L[i] <= R[j]:
            arr[k] = L[i]
            i += 1
        else:
            arr[k] = R[j]
            j += 1
        k += 1

    # Copy the remaining elements of L[],
    # if there are any
    while i < n1:
        arr[k] = L[i]
        i += 1
        k += 1

    # Copy the remaining elements of R[], 
    # if there are any
    while j < n2:
        arr[k] = R[j]
        j += 1
        k += 1

def merge_sort(arr, left, right):
    if left < right:
        mid = (left + right) // 2

        merge_sort(arr, left, mid)
        merge_sort(arr, mid + 1, right)
        merge(arr, left, mid, right)

    return arr




