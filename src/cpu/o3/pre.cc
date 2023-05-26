#include "cpu/o3/pre.hh"

#include "cpu/o3/dyn_inst.hh"

namespace gem5
{

namespace o3
{

SST::SST(CPU *_cpu, const BaseO3CPUParams &params)
    : cpu(_cpu),
      numEntries(params.numSSTEntries)
{
    assert(numEntries > 0);

    // L always has exactly numEntries elements.
    for (unsigned i = 0; i < numEntries; i++) {
        L.push_back(0);
    }
}

void
SST::addInst(Addr addr)
{
    AddrMapIter i = M.find(addr);

    // If x already exists, move it to the MRU position.
    if (i != M.end()) {
        L.splice(L.begin(), L, i->second);
    }

    // If x doesn't exists, insert it at the MRU position.
    else {
        // If SST is full, evict the LRU element first.
        if (M.size() == numEntries) {
            M.erase(L.back());
        }
        L.back() = addr;
        L.splice(L.begin(), L, --L.end());
        M[addr] = L.begin();
    }
}

void
SST::addInst(const DynInstPtr &inst)
{
    addInst(inst->pcState().instAddr());
}

bool
SST::hasInst(const DynInstPtr &inst)
{
    Addr addr = inst->pcState().instAddr();
    AddrMapIter i = M.find(addr);

    // If x exists, move it to the MRU position.
    if (i != M.end()) {
        L.splice(L.begin(), L, i->second);
        return true;
    }

    return false;
}

} // namespace o3
} // namespace gem5
