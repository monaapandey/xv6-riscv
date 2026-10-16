// xv6-RISC-V Kernel-level Semaphores Implementation

#include "kernel/types.h"
#include "kernel/riscv.h"
#include "kernel/defs.h"
#include "kernel/param.h"
#include "kernel/memlayout.h"
#include "kernel/spinlock.h"
#include "kernel/proc.h"

#define MAX_SEMS 32

struct semaphore {
  int value;
  int active;
  struct spinlock lock;
};

struct semaphore semtable[MAX_SEMS];

// Initialize semaphore table during kernel boot
void
sem_init_table(void)
{
  for (int i = 0; i < MAX_SEMS; i++) {
    initlock(&semtable[i].lock, "semaphore");
    semtable[i].value = 0;
    semtable[i].active = 0;
  }
}

// Allocate a new semaphore with an initial value
int
sem_alloc(int init_val)
{
  for (int i = 0; i < MAX_SEMS; i++) {
    acquire(&semtable[i].lock);
    if (!semtable[i].active) {
      semtable[i].active = 1;
      semtable[i].value = init_val;
      release(&semtable[i].lock);
      return i; // Return semaphore ID
    }
    release(&semtable[i].lock);
  }
  return -1; // No free semaphore available
}

// Semaphore Wait (P operation / Down)
int
sem_wait(int sem_id)
{
  if (sem_id < 0 || sem_id >= MAX_SEMS)
    return -1;

  struct semaphore *s = &semtable[sem_id];
  acquire(&s->lock);
  if (!s->active) {
    release(&s->lock);
    return -1;
  }

  // Using RISC-V xv6 sleep_prepare + sleep pattern
  while (s->value <= 0) {
    sleep_prepare(s);
    release(&s->lock);
    sleep();
    acquire(&s->lock);
    if (!s->active) {
      release(&s->lock);
      return -1;
    }
  }
  s->value--;
  release(&s->lock);
  return 0;
}

// Semaphore Post (V operation / Up)
int
sem_post(int sem_id)
{
  if (sem_id < 0 || sem_id >= MAX_SEMS)
    return -1;

  struct semaphore *s = &semtable[sem_id];
  acquire(&s->lock);
  if (!s->active) {
    release(&s->lock);
    return -1;
  }

  s->value++;
  wakeup(s);
  release(&s->lock);
  return 0;
}

// Free / Delete a semaphore
int
sem_free(int sem_id)
{
  if (sem_id < 0 || sem_id >= MAX_SEMS)
    return -1;

  struct semaphore *s = &semtable[sem_id];
  acquire(&s->lock);
  s->active = 0;
  s->value = 0;
  wakeup(s); // Wake up anyone waiting so they don't hang
  release(&s->lock);
  return 0;
}