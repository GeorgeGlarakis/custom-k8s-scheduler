# Time Complexity: O(n^2)
# Space Complexity: O(1)
def selectionSort(array, size, counter):
    
    for s in range(size):
        min_idx = s
        
        for i in range(s + 1, size):
            counter.count_comparison()
            # For sorting in descending order
            # for minimum element in each loop
            if array[i] < array[min_idx]:
                min_idx = i
                counter.count_swap()

        # Arranging min at the correct position
        (array[s], array[min_idx]) = (array[min_idx], array[s])
        counter.count_swap()

    return array

def main(array, counter):
    return selectionSort(array, len(array), counter)