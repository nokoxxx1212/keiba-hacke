import argparse

def is_prime(n):
    """
    素数判定を行う
    Args:
        n: 判定する整数
    Returns:
        bool: nが素数ならTrue, 素数でないならFalse
    """
    if n == 1:
        return False
    for k in range(2, n):
        if n % k == 0:
            return False
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Check if a number is prime.')
    parser.add_argument('--number', type=int, required=True, help='Number to check if it is prime.')
    args = parser.parse_args()

    if is_prime(args.number):
        print(f"{args.number} is prime")
    else:
        print(f"{args.number} is not prime")