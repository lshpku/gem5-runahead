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

MispTable::MispTable()
{
    for (int i = 0; i < table.size(); i++) {
        for (int j = 0; j < table[i].size(); j++) {
            table[i][j].lru = j;
        }
    }
}

void
MispTable::add(const DynInstPtr &inst)
{
    Addr pc = inst->pcState().instAddr();
    bool misp = inst->mispredicted();
    int rowIdx = (pc >> 1) & (table.size() - 1);
    auto &row = table[rowIdx];

    for (int i = 0; i < row.size(); i++) {
        // hit
        if (row[i].pc == pc) {
            row[i].ref++;
            if (misp)
                row[i].misp++;
            if (row[i].ref == MAX_REF) {
                row[i].ref >>= 1;
                row[i].misp >>= 1;
            }
            int lru = row[i].lru;
            for (int j = 0; j < row.size(); j++) {
                if (j != i && row[j].lru < lru)
                    row[j].lru++;
            }
            row[i].lru = 0;
            return;
        }
    }

    // not hit
    for (int i = 0; i < row.size(); i++) {
        if (row[i].lru == row.size() - 1) {
            row[i].pc = pc;
            row[i].lru = 0;
            row[i].ref = 1;
            row[i].misp = misp;
            for (int j = 0; j < row.size(); j++) {
                if (j != i)
                    row[j].lru++;
            }
        }
    }
}

bool
MispTable::high(const DynInstPtr &inst)
{
    Addr pc = inst->pcState().instAddr();
    int rowIdx = (pc >> 1) & (table.size() - 1);
    auto &row = table[rowIdx];
    for (int i = 0; i < row.size(); i++) {
        if (row[i].pc == pc) {
            return HIGH(row[i].ref, row[i].misp);
        }
    }
    return false;
}

} // namespace o3
} // namespace gem5
