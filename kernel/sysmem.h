#ifndef SYSMEM_H
#define SYSMEM_H

#include "types.h"

struct sys_mem_info {
  uint64 total_pages;
  uint64 free_pages;
  uint64 used_pages;
  uint64 alloc_events;
  uint64 free_events;
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