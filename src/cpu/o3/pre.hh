#ifndef __CPU_O3_PRE_HH__
#define __CPU_O3_PRE_HH__

#include <list>
#include <unordered_map>

#include "base/types.hh"
#include "config/the_isa.hh"
#include "cpu/inst_seq.hh"
#include "cpu/o3/dyn_inst_ptr.hh"

namespace gem5
{

struct BaseO3CPUParams;

namespace o3
{

class CPU;

/**
 * Stalling slice table class.
 */
class SST
{
    typedef std::list<Addr> AddrList;
    typedef AddrList::iterator AddrListIter;

    typedef std::unordered_map<Addr, AddrListIter> AddrMap;
    typedef AddrMap::iterator AddrMapIter;

    /** A hash list composed of addrList and addrMap. 
     *  This is for storing instructions and maintaining LRU order.
     */
    AddrList L;
    AddrMap M;

    /** Pointer to the CPU. */
    CPU *cpu;

    /** Number of instructions that SST can store. */
    unsigned numEntries;

  public:
    SST(CPU *_cpu, const BaseO3CPUParams &params);

    /** Adds an instruction of the stalling slice to SST.
     *  Newly added instructions may replace obsolate ones.
     */
    void addInst(Addr addr);
    void addInst(const DynInstPtr &inst);

    /** Determines if SST has this instruction. */
    bool hasInst(const DynInstPtr &inst);
};

/**
 * Precise register deallocation queue class.
 */
class PRDQ
{
};

} // namespace o3
} // namespace gem5

#endif //__CPU_O3_PRE_HH__
