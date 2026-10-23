# Blinded rating packet (50 bug reports)

Rate each report using the rubric in `research/methodology/human_target_validation_protocol.md`. Do not look anything up.

---

## H01

```
CORS preflight cache is skipped when `devtools.cache.disabled` is true

`devtools.cache.disabled` should only be used for remembering user's choice, so it should be not used at [here]([link]
Otherwise, the preflight cache is disabled when devtools is not opened.
```

---

## H02

```
Assertion failure: !aIsPreload, at /builds/worker/checkouts/gecko/uriloader/preload/PreloaderBase.cpp:135

Found with m-c 20260107-b9e21434cf45 (--enable-debug)

This was found by visiting a live website with a debug build.

STR:
- Launch browser and visit site

This issue was triggered by visiting `[link] A Pernosco session is available here: [link]

Assertion failure: !aIsPreload, at /builds/worker/checkouts/gecko/uriloader/preload/PreloaderBase.cpp:135
```

---

## H03

```
`int backlog` is assigned to `unsigned short sk_max_ack_backlog` -> overflow

I'm not sure that my analysis is correct, but:
sk_max_ack_backlog declared as unsigned short [email] [link]
and we're assigning `int backlog` to it [email] [link]

So if we'll set sysctls "net.ipv4.tcp_abort_on_overflow=1", "net.core.somaxconn=65536" (or larger) and backlog > 65536, we'll have real backlog = `somaxconn mod 65536`.

So AFAIU there shouldn't be possible to set somaxconn > 65535 or this behaviour should be fixed.
```

---

## H04

```
iwl3945: not only it periodically dies, it also BUG()s

Subject : ipw3945: not only it periodically dies, it also BUG()s
Submitter : Pavel Machek <[email]>
Date : 2008-02-05 22:44
References : [link]
Handled-By : "Chatre, Reinette" <[email]>

This entry is being used for tracking a regression from 2.6.24. Please don't
close it until the problem is fixed in the mainline.
```

---

## H05

```
Thunderbird 154: storage.local.get() fails during add-on startup with IndexedDB DirectoryLockFailed

error console thunderbird 154 startup-cleaned.txt

## Summary

A small number of users running Thunderbird 154 on Windows have encountered a persistent failure in QuotaManager / IndexedDB which prevents WebExtensions from reliably accessing `storage.local`.

The problem was initially reported as QuickFolders becoming stuck at “Initializing QuickFolders…”, but the attached error-console log shows that Thunderbird’s QuotaManager fails before the affected extensions initialize.

The issue appears to be rare and dependent on an unusual installation, filesystem, profile, update, or QuotaManager state.

## Reproducibility

I cannot reproduce this problem locally.

QuickFolders has thousands of users, and only a small number have reported this failure. The information in this report comes from affected installations and their error-console logs.

The observations below are not reliable reproduction steps.

## Environment

- Application: Thunderbird 154
- Operating system: Windows
- Affected extensions:
- QuickFolders
- quickFilters
- Initial QuickFolders test build: `QuickFolders-mx-6.17.1pre12.zip`
- Later test build with defensive storage retries: `QuickFolders-mx-6.17.1pre19.zip`

The complete error-console output is attached as a text file.

## Relevant errors

The attached log contains repeated QuotaManager initialization failures:

IndexedDB subsequently fails to obtain its directory lock:

Thunderbird then reports that the WebExtension storage.local migration cannot open its IndexedDB connection:

Thunderbird retains the older JSONFile backend:

Further extension-storage operations continue failing:

## Observed behavior

For the affected user:
1. QuickFolders stopped during initialization.
2. Restarting Thunderbird did not repair the problem.
3. Disabling quickFilters did not allow QuickFolders to initialize.
4.
```

---

## H06

```
Files corruption ( fs/ext4/inode.c:3941 ext4_set_page_dirty+0x3e/0x50 [ext4] )

Symptoms: after receiving the warning below I continued to work, but some processes with heavy I/O (namely g++), started to hang. I could kill them only via ctrl+c. The reboot program hanged too (no any reaction). Then I forced to turn off power and got corrupted files.

2019-11-04T12:31:44.706915+03:00 localhost kernel: [ 263.974691] WARNING: CPU: 3 PID: 138 at fs/ext4/inode.c:3941 ext4_set_page_dirty+0x3e/0x50 [ext4]
2019-11-04T12:31:44.706932+03:00 localhost kernel: [ 263.974694] Modules linked in: psmouse rfcomm 8021q garp mrp stp ctr ccm psnap llc cmac algif_hash algif_skcipher af_alg bnep joydev cor
etemp hwmon hid_multitouch hid_generic x86_pkg_temp_thermal intel_powerclamp kvm_intel i2c_designware_platform iTCO_wdt iTCO_vendor_support i2c_designware_core intel_rapl_msr mei_hdcp kvm ir
qbypass snd_soc_skl snd_soc_hdac_hda snd_hda_ext_core snd_soc_skl_ipc snd_soc_sst_ipc crct10dif_pclmul snd_soc_sst_dsp snd_soc_acpi_intel_match snd_soc_acpi ghash_clmulni_intel aesni_intel a
es_x86_64 snd_hda_codec_hdmi crypto_simd iwlmvm snd_soc_core cryptd snd_hda_codec_conexant glue_helper snd_hda_codec_generic snd_compress intel_cstate ledtrig_audio snd_pcm_dmaengine intel_r
apl_perf ac97_bus mac80211 snd_hda_intel hp_wmi input_leds sparse_keymap libarc4 wmi_bmof snd_hda_codec iwlwifi snd_hda_core uvcvideo snd_hwdep videobuf2_vmalloc i2c_i801 snd_pcm videobuf2_m
emops r8169 rtsx_pci_ms videobuf2_v4l2 memstick cfg80211 realtek videobuf2_common mei_me mei videodev btusb
2019-11-04T12:31:44.706938+03:00 localhost kernel: [ 263.974729] idma64 virt_dma btbcm btrtl intel_lpss_pci mc btintel intel_lpss intel_xhci_usb_role_switch processor_thermal_device roles
intel_soc_dts_iosf intel_rapl_common intel_pch_thermal battery int3403_thermal int340x_thermal_zone tpm_crb tpm_tis tpm_tis_core hp_accel lis3lv02d tpm input_polldev rng_core int3400_thermal
acpi_thermal_rel hp_wireless acpi_pad evdev ac mac_hid t
```

---

## H07

```
Make sure OHTTP config gets reloaded on connectivity change if first attempt failed.

It's possible that when the OHTTPService is loaded the network request fails.
We want to ensure that we retry fetching the config when the network is back up.
```

---

## H08

```
Incorrectly decoding IDN domain name as ISO-8859-1 instead of UTF-8

Zaslonska slika_20250904_225816.png

Steps to reproduce:

Open [link] and click on the first link. You need mumble installed. This is not relevant to mumble but you just somehow need to trigger the "Allow $ORIGIN to open the $SCHEME link with $APPLICATION?" security message.

[link] and [link] are of course different domains and can serve different documents.

Tested with user agent "Mozilla/5.0 (X11; Linux x86_64; rv:142.0) Gecko/20100101 Firefox/142.0" on Arch Linux.

Actual results:

Security warning message reads as follows: "Allow [link] to open the mumble link with Mumble?" The domain is incorrectly decoded as ISO-8859-1 instead of UTF-8.

See image with wrong decoding of domain name: [link]

Expected results:

Security warning message should read as follows: "Allow [link] to open the mumble link with Mumble?" The domain should be decoded as UTF-8.
```

---

## H09

```
WARNING: inconsistent lock state. inconsistent {SOFTIRQ-ON-W} -> {IN-SOFTIRQ-W} usage.

dmesg (5.1.0-rc7, Talos II)

I have not seen this on my amd64 machines on the 5.1-rcX kernels I've been running for some time, so I am filing this agains ppc64 platform specific.

I am running some zram-compressed swap space via systemd:
/sbin/zram-init -d0 -s32 -azstd -Lzram_swap 4096

Have not seen this in 5.0.x and before.

[...]
[ 313.402874] ================================
[ 313.402875] WARNING: inconsistent lock state
[ 313.402879] 5.1.0-rc7 #1 Not tainted
[ 313.402880] --------------------------------
[ 313.402882] inconsistent {SOFTIRQ-ON-W} -> {IN-SOFTIRQ-W} usage.
[ 313.402885] swapper/5/0 [HC0[0]:SC1[1]:HE1:SE0] takes:
[ 313.402888] 0000000080d1120c (&(&wsm.lock)->rlock){+.?.}, at: .zstd_reclaim_timer_fn+0x40/0x230
[ 313.402895] {SOFTIRQ-ON-W} state was registered at:
[ 313.402899] .lock_acquire+0xd0/0x240
[ 313.402903] ._raw_spin_lock+0x34/0x60
[ 313.402906] .zstd_get_workspace+0xd0/0x360
[ 313.402908] .end_compressed_bio_read+0x3b8/0x540
[ 313.402911] .bio_endio+0x174/0x2c0
[ 313.402914] .end_workqueue_fn+0x4c/0x70
[ 313.402917] .normal_work_helper+0x138/0x7e0
[ 313.402920] .process_one_work+0x324/0x790
[ 313.402922] .worker_thread+0x68/0x570
[ 313.402925] .kthread+0x19c/0x1b0
[ 313.402928] .ret_from_kernel_thread+0x58/0x78
[ 313.402930] irq event stamp: 2629216
[ 313.402933] hardirqs last enabled at (2629216): [<c0000000009da738>] ._raw_spin_unlock_irq+0x38/0x60
[ 313.402936] hardirqs last disabled at (2629215): [<c0000000009da4c4>] ._raw_spin_lock_irq+0x24/0x70
[ 313.402939] softirqs last enabled at (2629212): [<c0000000000af9fc>] .irq_enter+0x8c/0xd0
[ 313.402942] softirqs last disabled at (2629213): [<c0000000000afb58>] .irq_exit+0x118/0x170
[ 313.402944]
other info that might help us debug this:
[ 313.402945] Possible unsafe locking scenario:
```

---

## H10

```
The rtl-8187b card stops responding and connection is lost on hight trafic (torrent protocol).

The rtl8187 module driver doesn't work properly on hight traffic. When foe example I am downloading torrents the card doesn't respond an the connection is lost. I have to unload and load the module again. I only happens with me when the torrents are on.
```

---

## H11

```
few warnings during compiling 2.5.72

Distribution: Slackware 9.0
Hardware Environment: PC, [email] Mb:QDI KinetiZ
Software Environment:
Problem Description:During compining the 2.5.72 linux kernel i've had those
messages:

drivers/ide/ide-probe.c: In function `hwif_check_region':
drivers/ide/ide-probe.c:644: warning: `check_region' is deprecated (declared at

drivers/scsi/atp870u.c: In function `atp870u_detect':
drivers/scsi/atp870u.c:2374: warning: `check_region' is deprecated (declared at
drivers/scsi/atp870u.c:2446: warning: `check_region' is deprecated (declared at

drivers/pnp/resource.c: In function `pnp_check_port':
drivers/pnp/resource.c:298: warning: `check_region' is deprecated (declared at

I don't know what them means but I hope this report should be useful :-)

Good work!

bye :-)
```

---

## H12

```
Crash in [@ js::NewStringCopyN<T>]

Maybe Fission related. (DOMFissionEnabled=1)

Crash report: [link]

Reason:

Top 10 frames of crashing thread:

There are 3 crashes (from 3 installations) in nightly 97 starting with buildid 20211218213109. In analyzing the backtrace, the regression may have been introduced by patch [1] to fix bug 1746300.

[1] [link]
```

---

## H13

```
Unexpectedly long delay when searching via Google and HTTP/3 enabled

### Basic information

I have noticed for a few days that when doing a search via the built in Google search, I sometimes get a long delay. I used to work around it by doing the same search again (command-k, enter), but I took a few profiles today.

Steps to Reproduce:

1. Do a search via Command-k (separate search toolbar) or typing directly into address bar and hitting enter

Expected Results:

Very fast results.

Actual Results:

Multiple seconds waiting. Slow enough that I started to capture profiles while it was happening.

---

### More information

Profile URL: Two profiles from today:

* [link]
* [link]

#### Basic systems configuration:

OS version: macOS 10.15.7 (19H524)

GPU model: Intel HD Graphics 6000 1536 MB

Number of cores: 1.6 GHz Dual-Core Intel Core i5

Amount of memory (RAM): 4GB

Thanks so much for your help.
```

---

## H14

```
Parent Crash [@ nsHttpChannel::CancelInternal] via async ORB callback

test.html

# Null dereference in `nsHttpChannel::CancelInternal` via async ORB callback

## Summary

A remote server can crash the **Firefox parent process** with a null-pointer
dereference by serving a cross-origin `<script>` response that combines
`Transfer-Encoding: chunked` with a lying `Content-Length` header, triggering
`nsHttpChannel`'s concurrent-cache-write-interrupted recovery path which
`std::move()`s `mResponseHead` to null and falls through without restoring
it — after which the Opaque Response Blocker's async JavaScript-validation
callback fires, sets `mChannelBlockedByOpaqueResponse`, and calls `Cancel()`,
reaching an unguarded `mResponseHead->ClearHeaders()`.

| | |
|---|---|
| **File** | `netwerk/protocol/http/nsHttpChannel.cpp` |
| **Crash site** | Line 7445 (`mResponseHead->ClearHeaders()`) |
| **Root cause** | Line 10557 (`std::move(mResponseHead)`) + line 10581 fallthrough |
| **Bug class** | Null pointer dereference (parent process) |
| **ASan signature** | `SEGV on unknown address 0x000000000408` |
| **Reachable from** | Web content (cross-origin `<script src>`) |
| **Reproducer** | `brain/tests/nsHttpChannel/test.html` + `server.py` |
| **Default prefs** | All required prefs default-on for Desktop |

## The bug

### Crash site — `nsHttpChannel.cpp:7444-7446`

There is a sibling at `nsHttpChannel.cpp:10696-10698` with the same unguarded
pattern inside `ContinueOnStopRequest`.

### Root cause — `nsHttpChannel.cpp:10543-10586`

`MaybeSetupByteRangeRequest(size, contentLength, true)` fails when
`IsResumable(size, contentLength, true)` is false. `IsResumable` checks
`(partialLen < contentLength)` first — so when `size >= contentLength`, it
immediately returns false and we hit the fallthrough.

The code assumes "interrupted write" means `size < contentLength`.
```

---

## H15

```
Happy Eyeballs v3 adds ~250ms to cold connections on HTTP/3-capable sites when QUIC can't connect quickly

On a cold connection to an HTTP/3 origin, Happy Eyeballs v3 races h3/QUIC first and waits `network.http.happy-eyeballs.connection-attempt-delay` (250ms) before starting the h2/TCP attempt.

On Fenix Nightly I'm seeing that QUIC is slow and h3 doesn't finish in that window, so h2 starts ~250ms late and wins — every cold connection to an h3-advertising site pays ~250ms whether it ends up h2 or h3.

This profile is from Fenix Nightly via the playstore with no automation stack in the middle.

[link]

We can see the 250+ms delays to both [link] and [link]

Thank you to Kershaw and Max for helping to debug
```

---

## H16

```
http IPC locking issues

We don't take locks while reading/writing httprequesthead/httpresponsehead for IPC.

It's possible these happen to be safe (or some of them do), but it's hard to be certain of that.
```

---

## H17

```
Data race on HttpBaseChannel::mLoadFlags - written on cache I/O thread

OnCacheEntryCheck runs on the cache IO thread (CHECK_MULTITHREADED flag) and does mLoadFlags |= INHIBIT_CACHING, while the main thread may read mLoadFlags concurrently via GetLoadFlags().

The fix makes mLoadFlags Atomic<uint32_t, Relaxed> in HttpBaseChannel, matching the pattern already used for mStatus, mCanceled, TransferSize
etc. in the same class. Also updates SetCacheFlags() to accept the Atomic reference.

The write only triggers when a no-store cached response is loaded as read-only (offline back-navigation). The main thread is idle in the event loop during this window. On x86/ARM64 the aligned 32-bit RMW is HW-atomic. No security implications.
```

---

## H18

```
Heap use-after-free in [@ mozilla::net::TokenBucketCancelable::Fire] in the socket process via unvalidated nsresult in PHttpConnectionMgr::CancelTransaction

PHttpConnectionMgr::CancelTransaction(PHttpTransaction aTrans, nsresult aReason) carries a cancellation status that originates, unvalidated, from the content process: HttpChannelParent::RecvCancel accepts an arbitrary content-supplied nsresult and nsHttpChannel/HttpConnectionMgrParent relay it verbatim to the socket process. A compromised content process can therefore inject the internal sentinel failure code NS_BINDING_RETARGETED (0x804B0004), which content must never control: in the socket process, nsHttpTransaction::Close(NS_BINDING_RETARGETED) deliberately returns early (this sentinel is reserved for the WebSocket upgrade machinery to detach a transaction without closing it) and skips the mTokenBucketCancel->Cancel() cleanup.

The request-pacing token bucket (EventTokenBucket, enabled by default: network.http.pacing.requests.enabled=true, hz=80, burst=10) holds a TokenBucketCancelable whose mEvent member is a RAW ATokenBucketEvent* pointer to the nsHttpTransaction. The lifetime contract is that the transaction always cancels this entry from nsHttpTransaction::Close() before it can be destroyed. The injected sentinel breaks that contract: when the canceled channel is torn down, the PHttpTransaction actor's destruction (HttpTransactionChild::ActorDestroy, on the socket-process main thread) drops the last reference and ~nsHttpTransaction runs off the socket thread, where — in release builds, guarded only by a MOZ_DIAGNOSTIC_ASSERT that is compiled out — the cancelable is silently dropped without being canceled. The freed transaction's address remains queued in the token bucket; when the pacing timer next fires, TokenBucketCancelable::Fire() performs the virtual call mEvent->OnTokenBucketAdmitted() on the freed nsHttpTransaction.
```

---

## H19

```
In-memory corruption due to 974b1adc3b ("btrfs: use bio iterators for the decompression handlers")

Kernel config

TLDR: Bisection blames commit 974b1adc3b ("btrfs: use bio iterators for the decompression handlers") for consistent boot failures in 4.10-rc series. Reverting that commit in more recent kernels fixes the problem.

Let me know if you need more info, this is easy for me to reproduce.

Email exchange between Christoph Hellwig (author) and Liu Bo (reviewer) suggests to me that a mistake was spotted in the patch when it was sent to linux-btrfs. Was this fixed before it was sent to Linus?

[link]

Setting: /usr is a BTRFS filesystem with zlib compression. x86_64, SMP.

Symptoms: Shortly after the initramfs hands over to the root filesystem, some or all executables crash with segmentation faults, illegal instructions, sigabrt etc. For some reason the segfaults don't start immediately when init=/bin/bash but begin after a moderate number of btrfs filesystem accesses. Normal systemd boot is a reliable trigger. With init=/bin/bash, a bonnie++ run on another btrfs filesystem (i.e. a different filesystem to the one on /usr) seems to be a reliable trigger. Once the segfaults start, almost everything segfaults which makes debugging challenging. For some reason i686 binaries/libraries seem less likely to be affected than x86_64 binaries/libraries. There are no kernel warning messages, nothing of interest in dmesg, and bug manifestations seem to be entirely in userspace. Various kernel debug options including kasan, ubsan, debug_pagealloc and slub_debug=FZPU did not fix the problem or produce any kernel error messages. There does not seem to be any damage to the filesystem when subsequently using an unaffected kernel. Reverting the commit (identified by bisection) fixes the problem. My assumption is that in-memory corruption affects btrfs compressed extents after being decompressed (corruption of data in flight).
```

---

## H20

```
Crash in [@ mozilla::dom::quota::DropDirectoryLock]

Crash report: [link]

Reason:

Top 10 frames of crashing thread:

By querying Nightly crashes reported within the last 2 months, here are some insights about the signature:

- **First crash report:** 2024-06-15
- **Process type:** Parent
- **Is startup crash:** No
- **Has user comments:** No
- **Is null crash:** Yes - all crashes happened on null or near null memory address

By analyzing the backtrace, the regression may have been introduced by a patch [1] to fix Bug 1883353.

[1] [link]

:janv, since you are the author of the potential regressor, could you please take a look?
```

---

## H21

```
FIPS-mode crashes neqo

SUSE is currently having the following problem with FF91esr: When run in FIPS-mode, Firefox crashes in neqo.
As it turns out the call to hkdf::import_key(TLS_VERSION_1_3, cipher, salt) in new_initial() in third_party/rust/neqo-transport/src/crypto.rs fails, because it tries to create a key from raw key material, which is apparently not allowed in FIPS-mode.
```

---

## H22

```
[drivers/net/fs_enet/mii-fec.c]: Memory leaks for new_bus and fec

I think there are some possible memory leaks.

[drivers/net/fs_enet/mii-fec.c:197]: new_bus and fec
[drivers/net/fs_enet/mii-fec.c:306]: new_bus
[drivers/net/fs_enet/mii-fec.c:318]: new_bus and fec

This is the code on lines 181-197 where both new_bus and fec are leaked:

 new_bus = kzalloc(sizeof(struct mii_bus), GFP_KERNEL);
 if (!new_bus)
 goto out;

 fec = kzalloc(sizeof(struct fec_info), GFP_KERNEL);
 if (!fec)
 goto out_mii;

 new_bus->priv = fec;
 new_bus->name = "FEC MII Bus";
 new_bus->read = &fs_enet_fec_mii_read;
 new_bus->write = &fs_enet_fec_mii_write;
 new_bus->reset = &fs_enet_fec_mii_reset;

 ret = of_address_to_resource(ofdev->node, 0, &res);
 if (ret)
 return ret;

This is the code on lines 298-319 where both new_bus and fec are leaked:

 new_bus = kzalloc(sizeof(struct mii_bus), GFP_KERNEL);

 if (NULL == new_bus)
 return -ENOMEM;

 fec = kzalloc(sizeof(struct fec_info), GFP_KERNEL);

 if (NULL == fec)
 return -ENOMEM;

 new_bus->name = "FEC MII Bus",
 new_bus->read = &fs_enet_fec_mii_read,
 new_bus->write = &fs_enet_fec_mii_write,
 new_bus->reset = &fs_enet_fec_mii_reset,
 new_bus->id = pdev->id;

 pdata = (struct fs_mii_fec_platform_info *)pdev->dev.platform_data;

 if (NULL == pdata) {
 printk(KERN_ERR "fs_enet FEC mdio %d: Missing platform data!\n", pdev->id);
 return -ENODEV;
 }
```

---

## H23

```
With DoH, HEv3 races unreachable IPv6 first on cold connections, adding up to 40ms depending on the platform

This is what I'm observing on IPV4 only networks with DoH enabled, MacOS, and HeV3:

1. We attempt to connect by QUIC over IPV6 first (even though Firefox's connectivity service has failed to detect an ipv6 path `nsHttp — [Verbose] nsHttp: 134826b60 prefer ipv4=1, ipv6=0`)
2. Black hole -- we wait for 250ms, happy_eyeballs_connection_attempt_delay
3. We then try QUIC over IPV4, which succeeds
4. Once the IPV4 connection succeeds, we abort the IPv6 connection attempt
4. Example: cloudflare: [link]
5. And so it looks like every cold HTTP3 connection ends up being delayed by 250ms as we try IPV6 first
6. Example, from the same session: [link] : [link]
```

---

## H24

```
2.6.2* libata fails for sis 5513 PATA

Most recent kernel where this bug did not occur: none
Distribution: Gentoo
Hardware Environment: sis 630 chipset
Software Environment: x86
Problem Description:
i cannot boot a system with libata only (not old ide driver)

i enabled pata_sis and pata_generic support.
tried with irqroute and pci=noacpi options, no way.

when i try to suspend my notebook i have problems with ide controller.
the copy lasts a lot and i get oops with 2.6.17 kernel.

Stopping tasks: ==========================================|
Shrinking memory... done (22776 pages freed)
pnp: Device 00:08 disabled.
swsusp: Need to copy 30898 pages
ACPI: PCI Interrupt 0000:00:00.1[A]: no GSI - using IRQ 14
eth0: Media Link Off
ACPI: PCI Interrupt 0000:00: 01.2[D] -> Link [LNKD] -> GSI 5 (level,
low) -> IRQ 5
ACPI: PCI Interrupt 0000:00:01.3[D] -> Link [LNKD] -> GSI 5 (level,
low) -> IRQ 5
ACPI: PCI Interrupt 0000:00:01.4[B] -> Link [LNKB] -> GSI 5 (level,
low) -> IRQ 5
ACPI: PCI Interrupt 0000:00:01.6[B] -> Link [LNKB] -> GSI 5 (level,
low) -> IRQ 5
PCI: Setting latency timer of device 0000:00:02.0 to 64
PM: Writing back config space on device 0000:00:0a.0 at offset 1 (was
82100003, writing 82100007)
ACPI: PCI Interrupt 0000:00:0a.0[A] -> Link [LNKA] -> GSI 11 (level,
low) -> IRQ 11
PM: Writing back config space on device 0000:00:0a.1 at offset 1 (was
2100003, writing 82100007)
ACPI: PCI Interrupt 0000:00: 0a.1[B] -> Link [LNKC] -> GSI 5 (level,
low) -> IRQ 5
pnp: Device 00:08 activated.
pnp: Failed to activate device 00:0c.
pnp: Failed to activate device 00:0d.
```

---

## H25

```
Raid-0 causes kernel BUG at drivers/block/ll_rw_blk.c:1996

Distribution: RH 8.0
Hardware Environment: Athlon, AMD 761 (AMD North Bridge, VIA South bridge), IDE
Hard drives
Software Environment: Gnu C 3.2, Linux C Library 2.2.93, raidtools-1.00.2-3.3
Problem Description: 2.5.61 oops while trying to activate raid-0 volumes. Please
refer the thread
[link] for more
information from Neil Brown, [name] and Andrew Morton.

Steps to reproduce: Try to enable raid-0 volumes under 2.5.49 to 2.5.61

Sample oops:
------------[ cut here ]------------
kernel BUG at drivers/block/ll_rw_blk.c:1996!
invalid operand: 0000
CPU: 0
EIP: 0060:[<c02255d7>] Not tainted
EFLAGS: 00010246
EIP is at submit_bio+0x67/0x80
eax: 00000000 ebx: 00000000 ecx: 00000000 edx: df515804
esi: df515804 edi: 00001e74 ebp: c14d72e0 esp: df325d28
ds: 007b es: 007b ss: 0068
Process rpmq (pid: 161, threadinfo=df324000 task=df5a5440)
Stack: df9f9e04 df515804 c0188b1e 00000000 df515804 00001000 c0188de2 00000000
df515804 00001000 00000000 c0142d2f 00000001 dfd29d74 00000004 00004388
00000004 0000000a df17a0d4 00000010 df0e85fc df17a194 c14d72e0 00010901
Call Trace:
[<c0188b1e>] mpage_bio_submit+0x2e/0x40
[<c0188de2>] do_mpage_readpage+0x182/0x320
[<c0142d2f>] cache_alloc_debugcheck_after+0xaf/0xd0
[<c01c63df>] radix_tree_node_alloc+0x1f/0x60
[<c01c65d3>] radix_tree_insert+0x93/0xd0
[<c0189117>] mpage_readpage+0x37/0x60
[<c01a3430>] ext3_get_block+0x0/0xa0
[<c0139d89>] do_generic_mapping_read+0x1c9/0x3f0
[<c01a3430>] ext3_get_block+0x0/0xa0
[<c0139ff0>] file_read_actor+0x0/0xe0
[<c013a299>] __generic_file_aio_read+0x1c9/0x200
[<c0139ff0>] file_read_actor+0x0/0xe0
[<c013a32a>] generic_file_aio_read+0x5a/0x80
[<c015c9fc>] do_sync_read+0x8c/0xc0
[<c011801c>] do_page_fault+0x23c/0x457
[<c014e7a8>] do_brk+0x148/0x220
[<c015caec>] vfs_read+0xbc/0x130
[<c015ce68>] sys_pread64+0x58/0x80
[<c010a3af>] syscall_call+0x7/0xb

Code: 0f 0b cc 07 6e 7f 37 c0 eb aa 90 8d b4 26 00 00 00 00 8d bc
```

---

## H26

```
Wrong-thread crash handling a close message

[link]

Crash due to wrong-thread assertion in WebTransportSessionProxy::CloseSession(), called on Socket Thread.

Looks to be intermittent
```

---

## H27

```
Insert bay drive --> remove drive --> suspend --> resume fails

This is a Lenovo ThinkPad R61 7733A82 with a hotpluggable "Ultrabay"
DVD±RW/CD-RW drive.

If I remove the drive before booting and if I never insert it,
suspend/resume works. However, once I insert the drive (or if I start up
with the drive inserted), all future resumes will fail unless I insert the drive
before resuming.

Resume failures come in the form of a freeze about a second into the resume
process. The screen stays black, and the system is unresponsive to input - even
the magic sysreq keys don't work.

It's worth noting that hotplug is otherwise usable. I can even suspend the
system after inserting and then removing the drive, and resume will work as long
as I re-insert the drive before resume.

Latest working kernel version: never known to work
Earliest known failing kernel version: 2.6.26.3
Distribution: Ubuntu 8.04 amd64

Hardware Environment: lspci describes my ATA controller like so:
00:1f.0 ISA bridge: Intel Corporation 82801HBM (ICH8M-E) LPC Interface
Controller (rev 03)
00:1f.1 IDE interface: Intel Corporation 82801HBM/HEM (ICH8M/ICH8M-E) IDE
Controller (rev 03)
00:1f.2 SATA controller: Intel Corporation 82801HBM/HEM (ICH8M/ICH8M-E) SATA
AHCI Controller (rev 03)
00:1f.3 SMBus: Intel Corporation 82801H (ICH8 Family) SMBus Controller (rev
03)

Software Environment: sysfs tells me that the optical drive is under ata_piix,
and the hard drive is under ahci.
$ readlink /sys/block/sr0/device
../../devices/pci0000:00/0000:00:1f.1/host3/target3:0:0/3:0:0:0
$ readlink /sys/devices/pci0000:00/0000:00:1f.1/driver
../../../bus/pci/drivers/ata_piix
$ readlink /sys/block/sda/device
../../devices/pci0000:00/0000:00:1f.2/host0/target0:0:0/0:0:0:0
$ readlink /sys/devices/pci0000:00/0000:00:1f.2/driver
../../../bus/pci/drivers/ahci

I have libata's ACPI support enabled (/sys/module/libata/parameters/noacpi
== 0), and it appears that libata is managing Ultrabay hotswap.
```

---

## H28

```
Assertion failure: false, at /builds/worker/checkouts/gecko/netwerk/cookie/CookieServiceChild.cpp:319

Found with m-c 20250209-e71782bd0a2a (--enable-debug)

This was found by visiting a live website with a debug build.

STR:
- Launch browser and visit site

This issue was triggered by visiting `[link] A Pernosco session is available here: [link]

Assertion failure: false, at /builds/worker/checkouts/gecko/netwerk/cookie/CookieServiceChild.cpp:319
```

---

## H29

```
Crash in [@ mozilla::detail::nsTStringRepr<T>::First | HostIgnoredByProxy]

Crash report: [link]

MOZ_CRASH Reason:

Top 10 frames of crashing thread:

By querying Nightly crashes reported within the last 2 months, here are some insights about the signature:

- **First crash report:** 2025-08-09
- **Process type:** Parent
- **Is startup crash:** No
- **Has user comments:** No
- **Is null crash:** Yes - all crashes happened on null or near null memory address
```

---

## H30

```
Linux 6.4.4 Regression: MariaDB (mysqld) causes one core of the CPU to use 100% with io-wait operations.

OS: Arch Linux

Linux 6.4.4 introduces 100% usage in one core of the CPU with io-wait operations when MariaDB 11.0.2 (mysqld process) is running, even if the database is completely empty, this problem still occurs.

To prevent this bug for happening it is necessary to downgrade to Linux <6.4.3. Linux 6.4.4 without Arch Linux patches, Linux Mainline 6.5-rc1 and 6.5-rc2 don't fix the problem either.

Strangely there is also no sign that the mysqld process is using an absurd amount of io-wait on the processor core, it was found by purely discarding and killing processes until the processor core usage was normal and without io-wait operations. No tool to monitor I/O operations to find was able to find that mysqld was the cause of this bug (not even top).

I also used different commits prior to the 6.4.4 release using `git bisect` and none of them introduced this bug. There is no journal logs nor dmesg logs related to this bug. It independent of the file system used (I guess, it happens on EXT4 and BTRFS, but it doesn't seem to be related with the file system either)

How to reproduce it?:
- Install and use the Linux 6.4.4 Release
- Install MariaDB, initialize a empty database and run the process with your preferred init system
- Use htop or top to see the high io-wait usage in one core of the CPU

Arch Linux forums thread (Where we tested different kernel commits and there is other people with the same problem): [link]

If i need to provide more information, just ask for it...

(This bug was found originally because i use Akonadi, a PIM layer made by KDE Plasma developers that uses MariaDB/MySQL to store data)
```

---

## H31

```
Speculation rules prefetch is not used for navigation when the prefetch is still in flight

When a navigation starts while a matching speculation rules prefetch is still ongoing, the navigation should wait for it to complete (up to a timeout) and be served from the prefetch record, per [link]

Affected WPTs:
- speculation-rules/prefetch/navigation-timing-requestStart-responseStart.https.html?include=waitingForResponse
- speculation-rules/prefetch/navigation-timing-requestStart-responseStart.https.html?include=waitingForRedirect

Depends on Bug 2070841 since the slow executor responds with Cache-Control: no-store.
```

---

## H32

```
http:// navigation is upgraded to HTTPS via HTTPS RR (only with DoH enabled) and fails with no fallback on HTTP-only hosts

Firefox currently fails for me to load the [preview page for firefox-source-docs]([link] as linkified within Phabricator revisions. Note that this page is HTTP-only.

Steps:
1. Go to [link]
2. Click the link `file testing/perfdocs/generated/talos.md`

Actual result:
- Even though the link uses the `HTTP` scheme, Firefox upgrades the top-level navigation to `HTTPS` and attempts to connect on port 443.
- The host resets the connection (`PR_CONNECT_RESET_ERROR`, "Secure Connection Failed"), so the load fails and the page is never shown.

Expected result:
- Since the link is `http` and the host does not support HTTPS, the navigation should end up loading the page over HTTP instead of failing.

CC'ing Simon who was also able to reproduce the problem.
```

---

## H33

```
in any shell tested concatenation ">>" becomes ">"

This was discussed on #btrfs with user: darkling

Tested on sh bash zsh, erronously reported as also tested on fish

echo "test" > file && echo "testtest" >> file; cat file
testtest

instead of the expected
test
testtest

Rebooting with an earlier kernel 4.11 resolved the issue

Best Regards,

JL
```

---

## H34

```
Debug: sleeping function called from illegal context at include/linux/rwsem.h:43

Distribution: Debian Sarge
Hardware Environment: IBM Thinkpad 600

Problem Description:

When booting I get:

Debug: sleeping function called from illegal context at include/linux/rwsem.h:43
Call Trace:
[<c0116628>] __might_sleep+0x54/0x5c
[<c01cac71>] crypto_alg_lookup+0x21/0xc8
[<c01cbb3d>] crypto_alg_mod_lookup+0xd/0x30
[<c01cae2d>] crypto_alloc_tfm+0x11/0xc0
[<c02c40d0>] __ipv6_regen_rndid+0xa0/0x1f4
[<c0114ca1>] wake_up_process+0xd/0x14
[<c02c4252>] ipv6_regen_rndid+0x2e/0xc4
[<c011f099>] run_timer_softirq+0xf1/0x144
[<c02c4224>] ipv6_regen_rndid+0x0/0xc4
[<c011b8f1>] do_softirq+0x51/0xb0
[<c010a300>] do_IRQ+0x114/0x130
[<c0106f54>] default_idle+0x0/0x34
[<c0106f54>] default_idle+0x0/0x34
[<c0108ea8>] common_interrupt+0x18/0x20
[<c0106f54>] default_idle+0x0/0x34
[<c0106f54>] default_idle+0x0/0x34
[<c0106f7a>] default_idle+0x26/0x34
[<c0107009>] cpu_idle+0x35/0x44
[<c0105000>] rest_init+0x0/0x5c
[<c0105055>] rest_init+0x55/0x5c

__ipv6_regen_rndid(): too short regeneration interval; timer diabled for eth0.

Steps to reproduce:

The kernel is compiled with
[email] grep CRYPT .config
CONFIG_CRYPTO=y
CONFIG_CRYPTO_HMAC=y
CONFIG_CRYPTO_NULL=y
CONFIG_CRYPTO_MD4=m
CONFIG_CRYPTO_MD5=m
CONFIG_CRYPTO_SHA1=m
CONFIG_CRYPTO_SHA256=m
CONFIG_CRYPTO_SHA512=m
CONFIG_CRYPTO_DES=m
CONFIG_CRYPTO_BLOWFISH=m
CONFIG_CRYPTO_TWOFISH=m
CONFIG_CRYPTO_SERPENT=m
CONFIG_CRYPTO_AES=m
CONFIG_CRYPTO_TEST=m
[email] grep IPV6 .config
CONFIG_IPV6=y
CONFIG_IPV6_PRIVACY=y
```

---

## H35

```
Waiting for static.xx.fbcdn.net and Facebook Images Not Loading

+++ This bug was initially created as a clone of Bug #1735595 +++

Bug 1735595 landed a fix to not cache 408 responses.
Reporters indicate the problem is still happening (including with HTTP/2)
We'll use this bug to diagnose remaining issues.

[link]

@reporters: please take a look at the documentation above.
What would help in diagnosing these issues would be some HTTP logs when the bug happens:
[link]
```

---

## H36

```
[regression] iwlwifi: fails to connect - connection timeout

Upgrading to 5.6.0 leaves my work laptop without wifi, there seems to be three tries and a timeout - it never manages to connect.

It's a: HP EliteBook 840 G5

With:
01:00.0 Network controller: Intel Corporation Wireless 8265 / 8275 (rev 78)

Other laptop with a different driver works fine though...
```

---

## H37

```
ath9k: the signal power is about at 80% when under M$ Vista is at 100%

First, let me know which logs and info you need and I'll attach them to the next message. I'm not a wlan expert at all. At first I'll attach kernel.log and lspci -v.

The machine is a Dell Studio XPS 1340 with a AR928X PCI Express controller.

I'm one meter far from the AP (Zyxel 600 P series) and between the notebook and the AP there are only air.
With the pre-installed Windows Vista Home the connection to the network (WAP) is almost immediately established after giving the key and the signal power is at 100%.

With the Ubuntu 8.04 kernel, 2.6.27-7 and 2.6.27-14, the signal power was about between 60 amd 80%, then after the upgrade to Ubuntu 9.04 and kernel 2.6.28-11 the wireless network doesn't worked any more. Then I compiled a shiny vanilla 2.6.30 and the situation is that I have the signal power at 80% and the access to the network is quite slow (about 20 seconds). I recompiled enabling the debug for
ath9k. In the system log I don't see anomalies or errors.
```

---

## H38

```
sch_teql no longer works post 2.6.30

Patch to fix sch_teql

The sch_teql module, which can be used to load balance over a set of underlying interfaces, stopped working after 2.6.30 and has been broken in all kernels since then.

The problem is that the transmit routine relies on being able to access the destination address in the skb in order to do ARP resolution once it has decided which underlying interface it is going to transmit through.

In 2.6.31 the IFF_XMIT_DST_RELEASE flag was introduced, and set by default for all interfaces, which causes the destination address to be release before the transmit routine for the interface is called.

The solution (implemented in the attached patch) is to clear that flag for teql interfaces.
```

---

## H39

```
Firefox incorrectly interprets newlines in HTTP headers in HTTP/3, allowing for header splitting

Steps to reproduce:

1. Set up a system at [link] which speaks HTTP/3, and returns an HTTP/3 header with a newline in it.
2. Browse to it in Firefox with the Network tab open

Actual results:

The page loads properly and the Network tab indicates that Firefox parsed the header with a newline as two separate headers, similar to how it would have been parsed in HTTP/1.1

Expected results:

The page should fail to load, because the QPACK encoding for headers should allow Firefox to recognize that a single header containing a newline is present, and newlines are not allowed in headers.
```

---

## H40

```
Resume from suspend fails on intel 4965 AGN

Distribution: Ubuntu Lucid
Kernel version: 2.6.32.9.9
Environment used for testing: Dell XPS 1330 (All Intel)

All the info (lspci, dmesg....) are attached in the downstream bug report: [link]

I mark this as a regression because I have karmic installed too (2.6.31.16.29 kernel) and suspend/resume works.
```

---

## H41

```
autosuspend blacklist needed: Ralink RT2870 USB stick resets, stalls after disconnect/WPDMA TX/RX busy error

Every few days this USB device will spontaneously "disconnect", generate a WPDMA error and then reconnect as a full-speed device, but after the reset it does not function. It is connected to the rear onboard port on an Epox KT600 motherboard. Previously it was connected to an nForce3 motherboard and there was never a problem with it until moving it to the different motherboard.

Jan 31 13:04:48 iqrouter kernel: [106966.150750] usb 1-2: USB disconnect, device number 2
Jan 31 13:04:50 iqrouter kernel: [106967.772039] phy0 -> rt2800_wait_wpdma_ready: Error - WPDMA TX/RX busy [0xe0abd26c].
Jan 31 13:04:52 iqrouter kernel: [106968.036049] usb 1-2: new high-speed USB device number 3 using ehci_hcd
Jan 31 13:04:52 iqrouter dhcpd: receive_packet failed on wlan_priv0: Network is down
Jan 31 13:04:56 iqrouter last message repeated 2 times
Jan 31 13:05:05 iqrouter kernel: [106983.124124] hub 1-0:1.0: unable to enumerate USB device on port 2
Jan 31 13:05:08 iqrouter kernel: [106983.384049] usb 2-2: new full-speed USB device number 2 using uhci_hcd
Jan 31 13:05:08 iqrouter kernel: [106983.541968] usb 2-2: not running at top speed; connect to a high speed hub
Jan 31 13:05:08 iqrouter kernel: [106983.589958] usb 2-2: New USB device found, idVendor=148f, idProduct=3070
Jan 31 13:05:08 iqrouter kernel: [106983.597394] usb 2-2: New USB device strings: Mfr=1, Product=2, SerialNumber=3
Jan 31 13:05:08 iqrouter kernel: [106983.605257] usb 2-2: Product: 802.11 n WLAN
Jan 31 13:05:08 iqrouter kernel: [106983.610059] usb 2-2: Manufacturer: Ralink
Jan 31 13:05:08 iqrouter kernel: [106983.614660] usb 2-2: SerialNumber: 1.0
Jan 31 13:05:08 iqrouter kernel: [106983.744071] usb 2-2: reset full-speed USB device number 2 using uhci_hcd
Jan 31 13:05:08 iqrouter kernel: [106983.948098] ieee80211 phy1: Selected rate control algorithm 'minstrel_ht'
Jan 31 13:05:08 iqrouter kernel: [106983.948
```

---

## H42

```
With Cloudflare/NextDNS DoH enabled, It takes a long time (30s-1minute) for Firefox to realize that the internet has been disconnected.

Networking profile with logging: [link]
After the network had discinnected, i tried to load bmo. Firefox continued to try to load BMO for maybe a minute before it realizes that the internet is disconnected.

(FWIW, this repros both with/without "autodect proxy" settings)
```

---

## H43

```
fsync on file fails to persist the mode when one of its hard links is overwritten by a symbolic link

Proof of Concept

[Kernel version]
This bug can be reproduced on kernel 5.0.0-rc8.

[Reproduce]
* Use a VM, since our PoC simulates a crash by triggering a SysRq!
1. Download a base image (128 MB)
$ wget [link]

2. Mount the image
$ mkdir /tmp/btrfs
$ sudo mount -o loop btrfs-10.image /tmp/btrfs

3. Compile and run PoC
$ gcc poc.c -o poc
$ sudo ./poc /tmp/btrfs
(System reboots)

[Check]
1. Re-mount the crashed image
$ mkdir /tmp/btrfs
$ sudo mount -o loop btrfs-10.image /tmp/btrfs

2. Check inconsistency
$ stat /tmp/btrfs/foo/bar/hln
Access: (0644/-rw-r--r--)

[Description]
In the base image, 2 directories and 7 files exist.

0: 0755 (mount_point)
+--257: 0755 foo
+--258: 0755 bar
+--259: 0644 baz (12 bytes, offset: {})
+--259: 0644 hln (12 bytes, offset: {})
+--260: 0644 xattr (0 bytes, offset: {})
+--261: 0644 acl (0 bytes, offset: {})
+--262: 0644 æøå (4 bytes, offset: {})
+--263: 0644 fifo
+--264: 0777 sln -> mnt/foo/bar/baz

"./foo/bar/baz" and "./foo/bar/hln" are two hard links of inode #259.

Below is the breakdown of the PoC:
1. Open the mount_point direcotry,
(line 25) int fd_root = syscall(SYS_open, ".", O_DIRECTORY, 0);

2. create a symbolic link "foo/xxx", which points to "foo/bar/baz",
(line 26) syscall(SYS_symlink, "foo/bar/baz", "foo/xxx");

3. fsync the root directory,
(line 27) syscall(SYS_fsync, fd_root);

4. change permission of inode #259 ("foo/bar/baz" and "foo/bar/hln") to 0777,
(line 28) syscall(SYS_chmod, "foo/bar/baz", 0777);

5. rename the symlink "foo/xxx" to "foo/bar/baz",
(line 29) syscall(SYS_rename, "foo/xxx", "foo/bar/baz");

6. open and fsync inode #259 ("foo/bar/hln"), and
(line 30) int fd_hln = syscall(SYS_open, "foo/bar/hln", O_RDWR, 0);
(line 31) syscall(SYS_fsync, fd_hln);

7. simulate a crash by rebooting right away without un-mounting.
(line 35) system("echo b > /proc/sysrq-trigger");
```

---

## H44

```
Missing close in file generation sometimes causes build failures

Generated files [ascii_pac_utils.inc]([link] and [etld_data.inc]([link] sometimes don't get generated. Apparently, this is caused by makecppstring.py and prepare_tlds.py scripts sometimes not closing the files they are reading.
```

---

## H45

```
(ath5k) Not all elements of chinfo[pier].pd_curves[] are freed

Some of the memory blocks kcalloc'ed in
ath5k_eeprom_convert_pcal_info_*() are not freed even when module ath5k is
unloaded.

To reproduce the problem, it is enough to load ath5k.ko module and then unload it again.

Here is the trace for one iteration of the outer 'for' loop with my comments.
ath5k_eeprom_convert_pcal_info_2413(),
drivers/net/wireless/ath/ath5k/eeprom.c:1148:

// Allocation of chinfo[pier].pd_curves, line 1153. Room for 4 elements of
// type struct ath5k_pdgain_info is created.
called___kmalloc: (.text+0x212f) arguments: (48, 80d0), result: ab3ad780

// The inner loop, iter #0, allocation of pd->pd_step and pd->pd_pwr
// for chinfo[pier].pd_curves[pdgain_idx[0]] (lines 1176 and 1182)
called___kmalloc: (.text+0x212f) arguments: (4, 80d0), result: ab1c3f68
called___kmalloc: (.text+0x212f) arguments: (8, 80d0), result: ab1c3f70

// The inner loop, iter #1, allocation of pd->pd_step and pd->pd_pwr
// for chinfo[pier].pd_curves[pdgain_idx[1]] (lines 1176 and 1182)
called___kmalloc: (.text+0x212f) arguments: (5, 80d0), result: ab1c3f78
called___kmalloc: (.text+0x212f) arguments: (10, 80d0), result: ab17ce80
<...>

Here is the trace for one iteration of the outer 'for' loop,
ath5k_eeprom_free_pcal_info(),
drivers/net/wireless/ath/ath5k/eeprom.c:1564

// The inner loop, iter #0, line 1573
called_kfree: (.text+0x20be) arguments: ((null))
called_kfree: (.text+0x20c6) arguments: ((null))

// The inner loop, iter #1, line 1573
called_kfree: (.text+0x20be) arguments: (ab1c3f78)
called_kfree: (.text+0x20c6) arguments: (ab17ce80)

// Deallocation of chinfo[pier].pd_curves array
called_kfree: (.text+0x20de) arguments: (ab3ad780)
<...>

Same for other iterations of the outer 'for' loops in
ath5k_eeprom_convert_pcal_info_*() and ath5k_eeprom_free_pcal_info().

It looks like ath5k_eeprom_free_pcal_info() tries to free 'pd_step' and 'pd_pwr' fields of wrong elements.
```

---

## H46

```
In DnsAndConnectSocket::TransportSetup::ResolveHost(), we should not always dispatch a sync runnable to main thread

[DnsAndConnectSocket::TransportSetup::ResolveHost]([link] should be always be called on socket thread, so this means we always dispatch a sync runnable to main thread just for getting the DNS service.
```

---

## H47

```
rtl8188ee can't connect to a wireless network

Since kernel 3.15.x (used to work until 3.14.x) the wireless device rtl8188e doesn't work at all. It shows available wireless networks but when I try to connect to my home wireless network keeps trying to connect (and never acomplishes to connect).
lspci:

07:00.0 Network controller: Realtek Semiconductor Co., Ltd. RTL8188EE Wireless Network Adapter (rev 01)
08:00.0 Ethernet controller: Realtek Semiconductor Co., Ltd. RTL8101E/RTL8102E PCI Express Fast Ethernet controller (rev 07)

Until 3.14.x it worked. No config change or anything else. I run Arch Linux.
```

---

## H48

```
Support for Canyon CNP-WF518N3

patch

This USB Wifi adaptor uses Realtek RTL8188SU chipset, supported by r8192s_usb staging kernel module.

However small corrections should be made in the following file linux-2.6.32/drivers/staging/rtl8192su/r8192U_core.c in order to make device working.

I've made patch that adds support for this device.
```

---

## H49

```
Oops: tcp_retransmit_skb

Distribution:
Fedora

Hardware Environment:
Intel SHG2 Xeon Motherboard, 2 x 2.40GHz Xeon CPU, 4GB RAM, 1 x e100, 1 x e1000
(inactive)

lspci output:
00:00.0 Host bridge: ServerWorks CMIC-LE (rev 13)
00:00.1 Host bridge: ServerWorks CMIC-LE
00:00.2 Host bridge: ServerWorks: Unknown device 0000
00:02.0 VGA compatible controller: ATI Technologies Inc Rage XL (rev 27)
00:03.0 Ethernet controller: Intel Corp. 82557/8/9 [Ethernet Pro 100] (rev 0d)
00:0f.0 ISA bridge: ServerWorks CSB5 South Bridge (rev 93)
00:0f.1 IDE interface: ServerWorks CSB5 IDE Controller (rev 93)
00:0f.2 USB Controller: ServerWorks OSB4/CSB5 OHCI USB Controller (rev 05)
00:0f.3 Host bridge: ServerWorks GCLE Host Bridge
00:11.0 Host bridge: ServerWorks: Unknown device 0101 (rev 03)
00:11.2 Host bridge: ServerWorks: Unknown device 0101 (rev 03)
01:04.0 Ethernet controller: Intel Corp. 82544GC Gigabit Ethernet Controller
(LOM) (rev 02)
02:09.0 SCSI storage controller: Adaptec AIC-7899P U160/m (rev 01)
02:09.1 SCSI storage controller: Adaptec AIC-7899P U160/m (rev 01)

*Gigabit is not currently active (unplugged)

Software Environment:
Relatively busy caching proxy machine
```

---

## H50

```
brcmsmac: dmesg full of errors

After upgrade from 3.8 to 3.9 dmesg is full of these errors:
[12374.898305] brcmsmac bcma0:0: phyerr 0x1, rate 0x14
[12374.898311] brcmsmac bcma0:0: brcms_c_ampdu_dotxstatus_complete: ampdu tx phy error (0x1)
[12529.275861] brcmsmac bcma0:0: phyerr 0x10, rate 0x14
[12529.275887] brcmsmac bcma0:0: brcms_c_ampdu_dotxstatus_complete: ampdu tx phy error (0x10)

And TCP connections are disconnected very frequent.

My wi-fi card:
0d:00.0 Network controller: Broadcom Corporation BCM4313 802.11b/g/n Wireless LAN Controller (rev 01)
```

