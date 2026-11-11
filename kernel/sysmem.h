#ifndef SYSMEM_H
#define SYSMEM_H

#include "types.h"

struct sys_mem_info {
  uint64 total_pages;
  uint64 free_pages;
  uint64 used_pages;
  uint64 alloc_events;
  uint64 free_events;

  //Phase 3 Paging & Swapping Analytics
  int active_page_algo;  // 0 = FIFO, 1 = LRU
  uint64 page_faults;
  uint64 swap_outs;
};

struct proc_mem_info {
  int pid;
  uint64 asid;
  int is_thread;
  char name[16];
  uint64 vmem_sz;
  uint64 resident_pages;
  int state;
};

#endif