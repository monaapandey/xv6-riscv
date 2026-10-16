#include "types.h"
#include "riscv.h"
#include "defs.h"
#include "param.h"
#include "memlayout.h"
#include "spinlock.h"
#include "proc.h"
#include "vm.h"

uint64
sys_exit(void)
{
  int n;
  argint(0, &n);
  kexit(n);
  return 0; // not reached
}

uint64
sys_getpid(void)
{
  return myproc()->pid;
}

uint64
sys_fork(void)
{
  return kfork();
}

uint64
sys_wait(void)
{
  uint64 p;
  argaddr(0, &p);
  return kwait(p);
}

uint64
sys_sbrk(void)
{
  uint64 addr;
  int t;
  int n;

  argint(0, &n);
  argint(1, &t);
  addr = myproc()->sz;

  if (t == SBRK_EAGER || n < 0) {
    if (growproc(n) < 0) {
      return -1;
    }
  } else {
    // Lazily allocate memory for this process: increase its memory
    // size but don't allocate memory. If the processes uses the
    // memory, vmfault() will allocate it.
    if (addr + n < addr)
      return -1;
    if (addr + n > TRAPFRAME)
      return -1;
    myproc()->sz += n;
  }
  return addr;
}

uint64
sys_pause(void)
{
  int n;
  uint ticks0;

  argint(0, &n);
  if (n < 0)
    n = 0;
  acquire(&tickslock);
  ticks0 = ticks;
  while (ticks - ticks0 < n) {
    if (killed(myproc())) {
      release(&tickslock);
      return -1;
    }
    sleep_prepare(&ticks);
    release(&tickslock);
    sleep();
    acquire(&tickslock);
  }
  release(&tickslock);
  return 0;
}

uint64
sys_kill(void)
{
  int pid;

  argint(0, &pid);
  return kkill(pid);
}

// return how many clock tick interrupts have occurred
// since start.
uint64
sys_uptime(void)
{
  uint xticks;

  acquire(&tickslock);
  xticks = ticks;
  release(&tickslock);
  return xticks;
}
uint64
sys_set_priority(void)
{
  int pid, priority;
  
  argint(0, &pid);
  argint(1, &priority);
  
  if (priority < 0 || priority > 10)
    return -1;
    
  return set_priority(pid, priority);
}
// ==================== THREADS SYSCALLS ====================

uint64
sys_clone(void)
{
  uint64 fcn, arg, stack;
  
  // RISC-V mein user-space pointers 64-bit virtual addresses hote hain.
  // argaddr() unhe registers (a0, a1, a2) se safely fetch karta hai.
  argaddr(0, &fcn);
  argaddr(1, &arg);
  argaddr(2, &stack);
  
  return kclone(fcn, arg, stack);
}

uint64
sys_join(void)
{
  uint64 stack_addr;
  
  // User process address bhejti hai jahan exit hone wale thread 
  // ke stack ka base pointer save karna hai (taaki memory free ho sake).
  argaddr(0, &stack_addr);
  
  return kjoin(stack_addr);
}
uint64
sys_sleep(void)
{
  int n;
  uint ticks0;

  // argint void return karta hai isliye direct call karo
  argint(0, &n);

  acquire(&tickslock);
  ticks0 = ticks;
  while(ticks - ticks0 < n){
    if(killed(myproc())){
      release(&tickslock);
      return -1;
    }
    release(&tickslock);
    yield();
    acquire(&tickslock);
  }
  release(&tickslock);
  return 0;
}