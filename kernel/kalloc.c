// Physical memory allocator, for user processes,
// kernel stacks, page-table pages,
// and pipe buffers. Allocates whole 4096-byte pages.

#include "types.h"
#include "param.h"
#include "memlayout.h"
#include "spinlock.h"
#include "riscv.h"
#include "defs.h"
// Max RSS Pages allowed per process before eviction triggers
#define MAX_PROC_RSS 8

void freerange(void *pa_start, void *pa_end);

extern char end[]; // first address after kernel.
                   // defined by kernel.ld.

struct run {
  struct run *next;
};

struct {
  struct spinlock lock;
  struct run *freelist;
  uint64 total_pages;
  uint64 free_pages;
  uint64 alloc_events;
  uint64 free_events;
  //Phase 3 Memory Management
  int active_page_algo;
  uint64 page_faults;
  uint64 swap_outs;
} kmem;

void
kinit()
{
  initlock(&kmem.lock, "kmem");
  kmem.total_pages = (PHYSTOP - (uint64)end) / PGSIZE;
  kmem.free_pages = 0;
  freerange(end, (void *)PHYSTOP);
  
  // Reset events after boot initialization
  kmem.alloc_events = 0;
  kmem.free_events = 0;
  // Paging Initialization
  kmem.active_page_algo = 0; // Default: FIFO
  kmem.page_faults = 0;
  kmem.swap_outs = 0;
}
void increment_page_fault() {
  acquire(&kmem.lock);
  kmem.page_faults++;
  release(&kmem.lock);
}

// Function to handle swap outs (Evictions)
void trigger_page_eviction() {
  acquire(&kmem.lock);
  kmem.swap_outs++;
  release(&kmem.lock);
}

int set_page_algo(int algo) {
  if (algo < 0 || algo > 1) return -1;
  acquire(&kmem.lock);
  kmem.active_page_algo = algo;
  release(&kmem.lock);
  return 0;
}
void
freerange(void *pa_start, void *pa_end)
{
  char *p;
  p = (char *)PGROUNDUP((uint64)pa_start);
  for (; p + PGSIZE <= (char *)pa_end; p += PGSIZE)
    kfree(p);
}

// Free the page of physical memory pointed at by pa,
// which normally should have been returned by a
// call to kalloc().  (The exception is when
// initializing the allocator; see kinit above.)
void
kfree(void *pa)
{
  struct run *r;
  
  if (((uint64)pa % PGSIZE) != 0 || (char *)pa < end || (uint64)pa >= PHYSTOP)
    panic("kfree");

  memset(pa, 1, PGSIZE);
  
  r = (struct run *)pa;
  
  acquire(&kmem.lock);
  r->next = kmem.freelist;
  kmem.freelist = r;
  kmem.free_pages++;
  kmem.free_events++;
  release(&kmem.lock);
}

// Allocate one 4096-byte page of physical memory.
// Returns a pointer that the kernel can use.
// Returns 0 if the memory cannot be allocated.
void *
kalloc(void)
{
  struct run *r;
  acquire(&kmem.lock);
  r = kmem.freelist;
  if (r) {
    kmem.freelist = r->next;
    kmem.free_pages--;
    kmem.alloc_events++;
  }
  release(&kmem.lock);
  if (r)
    memset((char *)r, 5, PGSIZE);
  return (void *)r;
}

#include "sysmem.h"
void get_sys_meminfo(struct sys_mem_info *info) {
  acquire(&kmem.lock);
  info->total_pages = kmem.total_pages;
  info->free_pages = kmem.free_pages;
  info->used_pages = kmem.total_pages - kmem.free_pages;
  info->alloc_events = kmem.alloc_events;
  info->free_events = kmem.free_events;
  // Phase 3 stats copy
  info->active_page_algo = kmem.active_page_algo;
  info->page_faults = kmem.page_faults;
  info->swap_outs = kmem.swap_outs;
  release(&kmem.lock);
}