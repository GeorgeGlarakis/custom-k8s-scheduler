# Time Complexity: O(n*log(n))
# Space Complexity: O(log(n))
def merge(arr, left, mid, right, counter):
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
        counter.count_comparison()
        if L[i] <= R[j]:
            arr[k] = L[i]
            i += 1
            counter.count_comparison()
            counter.count_swap()
        else:
            arr[k] = R[j]
            j += 1
            counter.count_comparison()
            counter.count_swap()
        k += 1

    # Copy the remaining elements of L[],
    # if there are any
    while i < n1:
        arr[k] = L[i]
        i += 1
        k += 1
        counter.count_comparison()
        counter.count_swap()

    # Copy the remaining elements of R[], 
    # if there are any
    while j < n2:
        arr[k] = R[j]
        j += 1
        k += 1
        counter.count_comparison()
        counter.count_swap()

def merge_sort(arr, left, right, counter):
    if left < right:
        mid = (left + right) // 2

        merge_sort(arr, left, mid, counter)
        merge_sort(arr, mid + 1, right, counter)
        merge(arr, left, mid, right, counter)

    counter.count_comparison()
    return arr

def main(array, counter):
    return merge_sort(array, 0, len(array) - 1, counter)