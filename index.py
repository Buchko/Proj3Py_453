from dataclasses import dataclass

PAGE_TABLE_SIZE = 256
NUM_SIGNIFICANT_BITS = 16
OFFSET_SIZE = 8
PAGE_SIZE = 256



@dataclass
class PageTableEntry:
    frame: int
    isValid: bool


@dataclass
class Address:
    index: int
    offset: int


def parse_input(input_path):
    with open("adresses.txt", "r") as f:
        lines = f.readlines()
        lines = [line.strip() for line in lines]
        lines = [int(line) for line in lines]
    print(lines)


def parse_address(x: int) -> Address:
    masked_address = x & ((1 << NUM_SIGNIFICANT_BITS) - 1)
    offset = masked_address & ((1 << OFFSET_SIZE) - 1)
    index = masked_address >> OFFSET_SIZE

    ans = Address(index=index, offset=offset)
    return ans

def main():
    addresses = parse_input("adresses.txt")
    pageTable = [PageTableEntry(frame=-1, isValid=False) for _ in range(PAGE_TABLE_SIZE)]

    print(pageTable[0])


main()
