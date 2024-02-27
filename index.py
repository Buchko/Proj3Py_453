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
USE_TLB = True


@dataclass
class PageTableEntry:
    frame: int
    is_valid: bool


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
page_table = [PageTableEntry(frame=-1, is_valid=False) for _ in range(PAGE_TABLE_SIZE)]
# we just store an array of ints as a "page" for each page of memory at each page index
memory = [0] * NUM_FRAMES
frames = [-1] * NUM_FRAMES
logs = Logs(translated=0, faults=0, tlb_hits=0, tlb_misses=0)
tlb = TLB({}, 0, 5, [])
frame_queue = []


def read_page_from_store(page_index):
    starting_point = page_index * PAGE_SIZE
    with open("BACKING_STORE.bin", "rb") as f:
        f.seek(starting_point, os.SEEK_SET)
        page = f.read(PAGE_SIZE)
        page = array("B", page)
        page = list(page)
        return page


def parse_input(input_path):
    with open(input_path, "r") as f:
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


def fifo_replacement():
    victim_frame = frame_queue.pop(0)
    previous_page_num = frames[victim_frame]
    return victim_frame, previous_page_num


def get_free_frame(page_number):
    def insert_frame(frame_number, page_number):
        frames[frame_number] = page_number
        if REPLACEMENT_ALGORITHM == "fifo":
            frame_queue.append(frame_number)

    # searching for first free frame
    for i, frame in enumerate(frames):
        if frame == -1:
            insert_frame(i, page_number)
            return i
    # find victim frame
    match REPLACEMENT_ALGORITHM:
        case "fifo":
            replacer = fifo_replacement
        case _:
            replacer = fifo_replacement
    victim_frame, previous_page_num = replacer()
    insert_frame(victim_frame, page_number)
    page_table[previous_page_num].is_valid = False
    return victim_frame


def kick_out_victim():
    victim_page = tlb.fifo_queue.pop(0)
    del tlb.tlb[victim_page]
    page_table[victim_page].is_valid = False
    tlb.current_size -= 1


def add_to_tlb(page_index, entry):
    tlb.current_size += 1
    tlb.tlb[page_index] = entry
    tlb.fifo_queue.append(page_index)


def page_table_lookup(page_index):
    entry = page_table[page_index]
    if entry.is_valid:
        return entry, True
    # if it's invalid we need to read it in
    logs.faults += 1
    frame = get_free_frame(page_index)
    new_entry = PageTableEntry(frame=frame, is_valid=True)
    page_table[page_index] = new_entry
    page = read_page_from_store(page_index)
    memory[frame] = page
    return new_entry, False


def read_mem(frame, offset):
    page = memory[frame]
    read_value = page[offset]
    return page, read_value


def read(logical_address: int):
    parsed_address = parse_address(logical_address)
    page_index = parsed_address.index
    offset = parsed_address.offset
    # checking the tlb
    is_tlb_hit = USE_TLB and page_index in tlb.tlb and tlb.tlb[page_index].is_valid
    if is_tlb_hit:
        # tlb hit
        logs.tlb_hits += 1
        entry = tlb.tlb[page_index]
        frame = entry.frame
        page, read_value = read_mem(entry.frame, offset)
        did_hit = True
    else:
        # checking the page table
        logs.tlb_misses += 1
        entry, did_hit = page_table_lookup(page_index)
        frame = entry.frame
        page, read_value = read_mem(frame, offset)
        # updating the TLB
        if tlb.current_size == tlb.max_size:
            kick_out_victim()
        add_to_tlb(page_index, entry)

    logs.translated += 1
    # constructing output
    # converting the bytes array to a grouped hex string
    hexed_numbers = [f"{byte:02X}" for byte in page]
    hexed_numbers = "".join(hexed_numbers)
    output = f"{page_index}, {read_value}, {frame}, {is_tlb_hit}, {did_hit}, {hexed_numbers}"
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

    global memory
    memory = [0] * NUM_FRAMES
    global frames
    frames = [-1] * NUM_FRAMES

    addresses = parse_input(input_file)
    for addresses in addresses:
        print(read(addresses))
    output_logs()


if __name__ == "__main__":
    main()
