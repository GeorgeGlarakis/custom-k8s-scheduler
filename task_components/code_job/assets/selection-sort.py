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

def main(array):
    return selectionSort(array, len(array))

if __name__ == "__main__":
    my_array = [6, 3, 8, 9, 10, 1, 2, 11, 4, 5]
    print(main(my_array))