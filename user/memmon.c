#include "kernel/types.h"
#include "kernel/stat.h"
#include "kernel/sysmem.h"
#include "user/user.h"

int main(int argc, char *argv[]) {
  struct sys_mem_info smi;
  
  struct proc_mem_info *pmi = (struct proc_mem_info *)malloc(64 * sizeof(struct proc_mem_info));
  if (pmi == 0) {
    printf("memmon: malloc failed\n");
    exit(1);
  }

  printf("Memory Observatory Monitor Started...\n");

  while(1) {
    if (sysinfo(&smi) == 0) {
      // Added algo, faults, swaps to SYS_MEM_LOG
      printf("SYS_MEM_LOG: total=%d, free=%d, used=%d, allocs=%d, frees=%d, algo=%d, faults=%d, swaps=%d\n",
             (int)smi.total_pages, (int)smi.free_pages, (int)smi.used_pages, 
             (int)smi.alloc_events, (int)smi.free_events,
             smi.active_page_algo, (int)smi.page_faults, (int)smi.swap_outs);
    }

    int count = procinfo(pmi);
    for(int i = 0; i < count; i++) {
      printf("PROC_MEM_LOG: pid=%d, asid=%d, is_thread=%d, name=%s, vmem=%d, rpages=%d, state=%d\n",
             pmi[i].pid, (int)pmi[i].asid, pmi[i].is_thread, pmi[i].name, 
             (int)pmi[i].vmem_sz, (int)pmi[i].resident_pages, pmi[i].state);
    }

    sleep(50); 
  }
  exit(0);
}