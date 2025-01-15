# Time Complexity: O(n^2)
# Space Complexity: O(1)
def bubbleSort(arr, counter):
    
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
                counter.count_swap()

            counter.count_comparison()
                
    return arr

def main(array, counter):
    return bubbleSort(array, counter)