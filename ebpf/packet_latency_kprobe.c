// Reference eBPF probe for Linux packet latency experiments.
// It is intentionally kept as build-system-neutral source so the repo can be
// read on macOS while still showing the kernel/debugging path for Linux hosts.

#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <bpf/bpf_helpers.h>

struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 8192);
    __type(key, __u64);
    __type(value, __u64);
} packet_start SEC(".maps");

SEC("kprobe/netif_receive_skb")
int BPF_KPROBE(mark_packet_start, struct sk_buff *skb)
{
    __u64 key = (__u64)skb;
    __u64 now = bpf_ktime_get_ns();
    bpf_map_update_elem(&packet_start, &key, &now, BPF_ANY);
    return 0;
}

SEC("kprobe/dev_queue_xmit")
int BPF_KPROBE(report_packet_latency, struct sk_buff *skb)
{
    __u64 key = (__u64)skb;
    __u64 *start = bpf_map_lookup_elem(&packet_start, &key);

    if (start) {
        __u64 delta_us = (bpf_ktime_get_ns() - *start) / 1000;
        if (delta_us > 5000) {
            bpf_printk("edgeprobe packet latency skb=%llx latency_us=%llu", key, delta_us);
        }
        bpf_map_delete_elem(&packet_start, &key);
    }

    return 0;
}

char LICENSE[] SEC("license") = "GPL";

