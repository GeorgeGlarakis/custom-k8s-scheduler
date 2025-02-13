# Time Complexity: O(n^2)
# Space Complexity: O(1)
def insertion_sort(arr, counter):
  
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

            counter.count_comparison()
            counter.count_swap()
            
        arr[j + 1] = a  

        counter.count_comparison()
        counter.count_swap()
        
    return arr

def main(array, counter):
    return insertion_sort(array, counter)