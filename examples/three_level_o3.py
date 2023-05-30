import sys
import argparse
import builtins
import m5
from m5.objects import O3CPU
from m5.objects import Cache, MemCtrl, SystemXBar, L2XBar, DDR3_1600_8x8, AddrRange
from m5.objects import Process, Root, SEWorkload, System, SrcClockDomain, VoltageDomain
from m5.objects import StridePrefetcher, SignaturePathPrefetcher
from m5.objects.BranchPredictor import TAGE_SC_L_8KB

parser = argparse.ArgumentParser()
parser.add_argument('--pre', action='store_true')
parser.add_argument('--pre-br', action='store_true')
parser.add_argument('--mj', action='store_true')
parser.add_argument('--spp', action='store_true')
parser.add_argument('--bop', action='store_true')
parser.add_argument('--drain', action='store_true')
parser.add_argument('command')
parser.add_argument('options', nargs=argparse.REMAINDER)
args = parser.parse_args()


def print(*args):
    msg = ' '.join(str(arg) for arg in args)
    if sys.stderr.isatty():
        msg = '\033[93m' + msg + '\033[0m'
    builtins.print(msg, file=sys.stderr)


print('command:', repr(args.command))
print('options:', *(repr(i) for i in args.options))


class L1Cache(Cache):
    assoc = 2
    tag_latency = 2
    data_latency = 2
    response_latency = 2
    mshrs = 8
    tgts_per_mshr = 20


class L1ICache(L1Cache):
    size = '32kB'


class L1DCache(L1Cache):
    size = '32kB'


class L2Cache(Cache):
    size = '256kB'
    assoc = 8
    tag_latency = 8
    data_latency = 8
    response_latency = 20
    mshrs = 16
    tgts_per_mshr = 12

    if args.bop:
        prefetcher = StridePrefetcher()
    if args.spp:
        prefetcher = SignaturePathPrefetcher()
    prefetch_on_pf_hit = True


class L3Cache(Cache):
    size = '1MB'
    assoc = 16
    tag_latency = 20
    data_latency = 20
    sequential_access = True
    response_latency = 40
    mshrs = 32
    tgts_per_mshr = 12
    write_buffers = 16


class PageTableWalkerCache(Cache):
    assoc = 2
    tag_latency = 2
    data_latency = 2
    response_latency = 2
    mshrs = 10
    size = '4kB'
    tgts_per_mshr = 12


system = System()

system.clk_domain = SrcClockDomain()
system.clk_domain.clock = '2.66GHz'
system.clk_domain.voltage_domain = VoltageDomain()

system.mem_mode = 'timing'
system.mem_ranges = [AddrRange('2GB')]

system.cpu = O3CPU()

system.cpu.branchPred = TAGE_SC_L_8KB()

system.cpu.decodeWidth = 8
system.cpu.renameWidth = 4
system.cpu.dispatchWidth = 4
system.cpu.issueWidth = 4
system.cpu.wbWidth = 4
system.cpu.commitWidth = 4
system.cpu.squashWidth = 4

system.cpu.numIQEntries = 92
system.cpu.LQEntries = 64
system.cpu.SQEntries = 64
system.cpu.numPhysIntRegs = 168
system.cpu.numPhysFloatRegs = 168

system.cpu.numROBEntries = 64
system.cpu.numPRDQEntries = 192
system.cpu.enablePRE = args.pre or args.pre_br
system.cpu.enablePREBranch = args.pre_br
system.cpu.enableMJ = args.mj

# Increase this if IEW::instToCommit() causes overflow (default is 5).
system.cpu.forwardComSize = 10

system.cpu.icache = L1ICache()
system.cpu.dcache = L1DCache()

system.cpu.icache.cpu_side = system.cpu.icache_port
system.cpu.dcache.cpu_side = system.cpu.dcache_port

# RISCV requires TLB walker cache
system.cpu.itb_walker_cache = PageTableWalkerCache()
system.cpu.dtb_walker_cache = PageTableWalkerCache()
system.cpu.mmu.connectWalkerPorts(
    system.cpu.itb_walker_cache.cpu_side,
    system.cpu.dtb_walker_cache.cpu_side)

system.l2bus = L2XBar()

system.cpu.icache.mem_side = system.l2bus.cpu_side_ports
system.cpu.dcache.mem_side = system.l2bus.cpu_side_ports

system.cpu.itb_walker_cache.mem_side = system.l2bus.cpu_side_ports
system.cpu.dtb_walker_cache.mem_side = system.l2bus.cpu_side_ports

system.l2cache = L2Cache()
system.l2cache.cpu_side = system.l2bus.mem_side_ports

system.l3bus = L2XBar()
system.l2cache.mem_side = system.l3bus.cpu_side_ports

system.l3cache = L3Cache()
system.l3cache.cpu_side = system.l3bus.mem_side_ports

system.membus = SystemXBar()

system.l3cache.mem_side = system.membus.cpu_side_ports

system.cpu.createInterruptController()

# For x86 only, make sure the interrupts are connected to the memory
# Note: these are directly connected to the memory bus and are not cached
if m5.defines.buildEnv['TARGET_ISA'] == "x86":
    system.cpu.interrupts[0].pio = system.membus.mem_side_ports
    system.cpu.interrupts[0].int_requestor = system.membus.cpu_side_ports
    system.cpu.interrupts[0].int_responder = system.membus.mem_side_ports

system.system_port = system.membus.cpu_side_ports

system.mem_ctrl = MemCtrl()
system.mem_ctrl.dram = DDR3_1600_8x8()
system.mem_ctrl.dram.range = system.mem_ranges[0]
system.mem_ctrl.port = system.membus.mem_side_ports

system.workload = SEWorkload.init_compatible(args.command)

process = Process()
process.cmd = [args.command, *args.options]
system.cpu.workload = process
system.cpu.createThreads()

root = Root(full_system=False, system=system)
m5.instantiate()

print("Beginning simulation")
cause_slice = 'reach slice limit'

while True:
    # system.cpu.scheduleInstStop(0, 1000000, cause_slice)
    exit_event = m5.simulate()
    exit_cause = exit_event.getCause()
    inst_count = system.cpu.getCurrentInstCount(0)

    if exit_cause != cause_slice:
        break

    print('Pause @ tick %i inst %i because %s' % (m5.curTick(), inst_count, exit_cause))

print('Exiting @ tick %i inst %i because %s' % (m5.curTick(), inst_count, exit_cause))
if args.drain:
    m5.drain()
exit(exit_event.getCode())
