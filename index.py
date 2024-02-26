import os
import sys
from dataclasses import dataclass
from array import array
import argparse

PAGE_TABLE_SIZE = 256
NUM_SIGNIFICANT_BITS = 16
OFFSET_SIZE = 8
PAGE_SIZE = 256
NUM_FRAMES = 256
REPLACEMENT_ALGORITHM = "fifo"


@dataclass
class PageTableEntry:
    frame: int
    isValid: bool


@dataclass
class Address:
    index: int
    offset: int


@dataclass
class Logs:
    translated: int
    faults: int
    tlb_hits: int
    tlb_misses: int


@dataclass
class TLB:
    tlb: {}
    current_size: int
    max_size: int
    fifo_queue: []


# whee global variables
page_table = [PageTableEntry(frame=-1, isValid=False) for _ in range(PAGE_TABLE_SIZE)]
# we just store an array of ints as a "page" for each page of memory at each page index
memory = [0] * NUM_FRAMES
frames = [0] * NUM_FRAMES
logs = Logs(translated=0, faults=0, tlb_hits=0, tlb_misses=0)
tlb = TLB({}, 0, 16, [])


def read_page_from_store(page_index):
    starting_point = page_index * PAGE_SIZE
    with open("BACKING_STORE.bin", "rb") as f:
        f.seek(starting_point, os.SEEK_SET)
        page = f.read(PAGE_SIZE)
        page = array("B", page)
        page = list(page)
        return page


def parse_input(input_path):
    with open("addresses.txt", "r") as f:
        lines = f.readlines()
        lines = [line.strip() for line in lines]
        lines = [int(line) for line in lines]
    return lines


def parse_address(x: int) -> Address:
    masked_address = x & ((1 << NUM_SIGNIFICANT_BITS) - 1)
    offset = masked_address & ((1 << OFFSET_SIZE) - 1)
    index = masked_address >> OFFSET_SIZE

    ans = Address(index=index, offset=offset)
    return ans


def get_free_frame():
    for i, frame in enumerate(frames):
        if frame == 0:
            frames[i] = 1
            return i
    print("out of memory")
    sys.exit(1)


def kick_out_victim():
    victim_page = tlb.fifo_queue.pop(0)
    del tlb.tlb[victim_page]


def add_to_tlb(page_index, page):
    tlb.tlb[page_index] = page
    tlb.fifo_queue.append(page_index)

def page_table_lookup(page_index):
    entry = page_table[page_index]
    if entry.isValid:
        frame = entry.frame
        page = memory[frame]
        return frame, page
    else:
        logs.faults += 1
        frame = get_free_frame()
        new_entry = PageTableEntry(frame=frame, isValid=True)
        page_table[page_index] = new_entry
        page = read_page_from_store(page_index)
        memory[frame] = page
    return frame, page


def read(logical_address: int):
    parsed_address = parse_address(logical_address)
    page_index = parsed_address.index
    offset = parsed_address.offset
    # checking the tlb
    if page_index in tlb.tlb:
        # tlb hit
        logs.tlb_hits += 1
        frame = tlb.tlb[page_index]
        page = memory[frame]
    else:
        # checking the page table
        logs.tlb_misses += 1
        frame, page = page_table_lookup(page_index)
        # updating the TLB
        if tlb.current_size == tlb.max_size:
            kick_out_victim()
        add_to_tlb(page_index, frame)

    logs.translated += 1
    read_value = page[offset]

    # constructing output
    # converting the bytes array to a grouped hex string
    hexed_numbers = [f"{byte:02X}" for byte in page]
    hexed_numbers = "".join(hexed_numbers)
    output = f"{logical_address}, {read_value}, {frame}, {hexed_numbers}"
    return output


def output_logs():
    print(f"Number of Translated Addresses = {logs.translated}")
    print(f"Page Faults = {logs.faults}")
    print(f"TLB Hits = {logs.tlb_hits}")
    print(f"TLB Misses = {logs.tlb_misses}")
    hit_rate = logs.tlb_hits / (logs.tlb_hits + logs.tlb_misses)
    hit_rate = round(hit_rate, 3)
    print(f"TLB Hit Rate = {hit_rate}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", type=str)
    parser.add_argument("num_frames", type=int, default=256, nargs="?")
    parser.add_argument("pra", type=str, default="fifo", nargs="?")
    args = parser.parse_args()
    input_file = args.input_file
    global NUM_FRAMES
    NUM_FRAMES = args.num_frames
    global REPLACEMENT_ALGORITHM
    REPLACEMENT_ALGORITHM = args.pra
    addresses = parse_input(input_file)
    for addresses in addresses:
        print(read(addresses))
    output_logs()


if __name__ == "__main__":
    main()
